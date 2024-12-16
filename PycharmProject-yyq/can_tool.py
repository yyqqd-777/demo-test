import sys
import can
import logging
import queue
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QComboBox, QTableWidget, 
                            QTableWidgetItem, QLabel, QTextEdit, QTabWidget)
from PyQt6.QtCore import QTimer, pyqtSignal, QThread
import serial.tools.list_ports  # 用于检测串口
import canopen
import time

# 设置日志配置
logging.basicConfig(
    filename='can_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

class CANWorker(QThread):
    """CAN通信工作线程"""
    message_received = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, channel='can0', bitrate=500000):
        super().__init__()
        self.channel = channel
        self.bitrate = bitrate
        self.running = False
        self.bus = None

    def run(self):
        try:
            self.bus = can.interface.Bus(
                channel=self.channel,
                bustype='slcan',
                bitrate=self.bitrate
            )
            self.running = True
            
            while self.running:
                message = self.bus.recv(timeout=0.1)
                if message:
                    self.message_received.emit(message)
                    
        except Exception as e:
            self.error_occurred.emit(str(e))
            logging.error(f"CAN通信错误: {e}")

    def stop(self):
        self.running = False
        if self.bus:
            self.bus.shutdown()

class CANMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('CAN总线监控工具')
        self.setGeometry(100, 100, 1200, 800)
        self.can_worker = None
        self.message_queue = queue.Queue()
        self.initUI()

    def initUI(self):
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # 监控页面
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(monitor_tab)
        
        # 控制面板
        control_panel = QHBoxLayout()
        
        # 接口选择
        self.interface_combo = QComboBox()
        control_panel.addWidget(QLabel('串口:'))
        control_panel.addWidget(self.interface_combo)
        
        # 波特率选择
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(['125000', '250000', '500000', '1000000'])
        control_panel.addWidget(QLabel('波特率:'))
        control_panel.addWidget(self.bitrate_combo)
        
        # 开始/停止按钮
        self.start_button = QPushButton('开始监控')
        self.start_button.clicked.connect(self.toggle_monitoring)
        control_panel.addWidget(self.start_button)
        
        # 扫描节点按钮
        scan_button = QPushButton('扫描节点')
        scan_button.clicked.connect(self.scan_nodes)
        control_panel.addWidget(scan_button)
        
        monitor_layout.addLayout(control_panel)
        
        # 消息表格
        self.message_table = QTableWidget()
        self.message_table.setColumnCount(7)
        self.message_table.setHorizontalHeaderLabels(
            ['时间戳', '节点ID', '类型', '长度', '数据', '解析值', '状态'])
        monitor_layout.addWidget(self.message_table)
        
        # 添加监控页面
        tab_widget.addTab(monitor_tab, "实时监控")
        
        # 节点配置页面
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)
        
        # 节点列表
        self.node_table = QTableWidget()
        self.node_table.setColumnCount(4)
        self.node_table.setHorizontalHeaderLabels(['节点ID', '状态', '波特率', '操作'])
        config_layout.addWidget(self.node_table)
        
        tab_widget.addTab(config_tab, "节点配置")
        
        # 日志页面
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        tab_widget.addTab(log_tab, "日志")

        # 状态栏
        self.statusBar().showMessage('就绪')

    def toggle_monitoring(self):
        if not self.can_worker:
            # 开始监控
            channel = self.interface_combo.currentText()
            bitrate = int(self.bitrate_combo.currentText())
            
            try:
                self.can_worker = CANWorker(channel, bitrate)
                self.can_worker.message_received.connect(self.process_message)
                self.can_worker.error_occurred.connect(self.handle_error)
                self.can_worker.start()
                
                self.start_button.setText('停止监控')
                self.statusBar().showMessage('正在监控CAN总线...')
                logging.info(f"开始监控CAN总线 - 接口: {channel}, 波特率: {bitrate}")
                
            except Exception as e:
                self.handle_error(str(e))
                
        else:
            # 停止监控
            self.can_worker.stop()
            self.can_worker = None
            self.start_button.setText('开始监控')
            self.statusBar().showMessage('监控已停止')
            logging.info("停止监控CAN总线")

    def process_message(self, msg):
        """处理接收到的CAN消息"""
        row = self.message_table.rowCount()
        self.message_table.insertRow(row)
        
        # 添加消息数据到表格
        timestamp = datetime.fromtimestamp(msg.timestamp).strftime('%H:%M:%S.%f')[:-3]
        self.message_table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.message_table.setItem(row, 1, QTableWidgetItem(f"0x{msg.arbitration_id:X}"))
        self.message_table.setItem(row, 2, QTableWidgetItem('RTR' if msg.is_remote_frame else 'DATA'))
        self.message_table.setItem(row, 3, QTableWidgetItem(str(msg.dlc)))
        
        # 将数据转换为十六进制字符串
        data_hex = ' '.join(f"{b:02X}" for b in msg.data[:msg.dlc])
        self.message_table.setItem(row, 4, QTableWidgetItem(data_hex))
        
        # 尝试解析数据
        try:
            parsed_value = self.parse_can_data(msg)
            self.message_table.setItem(row, 5, QTableWidgetItem(parsed_value))
        except Exception as e:
            self.message_table.setItem(row, 5, QTableWidgetItem("解析错误"))
        
        self.message_table.setItem(row, 6, QTableWidgetItem("正常"))
        
        # 记录日志
        log_msg = f"接收: ID=0x{msg.arbitration_id:X}, 数据={data_hex}"
        logging.info(log_msg)
        self.log_text.append(f"{timestamp} - {log_msg}")

    def parse_can_data(self, msg):
        """解析CAN数据"""
        # 这里可以根据不同的CAN ID实现不同的解析逻辑
        if msg.arbitration_id == 0x141:  # 电机状态1
            return f"温度={msg.data[0]}°C, 电压={msg.data[1]/10.0}V"
        elif msg.arbitration_id == 0x142:  # 电机状态2
            speed = int.from_bytes(msg.data[2:4], byteorder='little', signed=True)
            return f"速度={speed}rpm"
        return "未知数据格式"

    def scan_nodes(self):
        """扫描CAN节点"""
        if not self.interface_combo.currentText():
            self.statusBar().showMessage('请选择串口设备')
            logging.warning("未选择串口设备")
            return
        
        self.statusBar().showMessage('正在扫描节点...')
        logging.info("开始扫描CAN节点")
        
        # 清空节点表格
        self.node_table.setRowCount(0)
        
        try:
            # 创建CANopen网络
            network = canopen.Network()
            channel = self.interface_combo.currentText()
            bitrate = int(self.bitrate_combo.currentText())
            
            # 连接到CAN网络
            network.connect(channel=channel, bustype='slcan', bitrate=bitrate)
            time.sleep(0.5)  # 等待连接稳定
            
            # 扫描节点
            for node_id in network.scanner.nodes:
                row = self.node_table.rowCount()
                self.node_table.insertRow(row)
                
                self.node_table.setItem(row, 0, QTableWidgetItem(f"0x{node_id:X}"))
                self.node_table.setItem(row, 1, QTableWidgetItem("在线"))
                self.node_table.setItem(row, 2, QTableWidgetItem(f"{bitrate/1000}k"))
                
                config_button = QPushButton("配置")
                config_button.clicked.connect(lambda checked, nid=node_id: self.configure_node(nid))
                self.node_table.setCellWidget(row, 3, config_button)
                
                logging.info(f"发现节点: 0x{node_id:X}")
            
            # 断开连接
            network.disconnect()
            
            if self.node_table.rowCount() == 0:
                self.statusBar().showMessage('未发现活动节点')
                logging.info("扫描完成：未发现活动节点")
            else:
                self.statusBar().showMessage(f'扫描完成，发现 {self.node_table.rowCount()} 个节点')
                logging.info(f"扫描完成：发现 {self.node_table.rowCount()} 个活动节点")
                
        except Exception as e:
            error_msg = f"节点扫描出错: {str(e)}"
            self.statusBar().showMessage(error_msg)
            logging.error(error_msg)

    def configure_node(self, node_id):
        """配置节点"""
        logging.info(f"配置节点 0x{node_id:X}")
        # 这里实现节点配置逻辑

    def handle_error(self, error_msg):
        """处理错误"""
        self.statusBar().showMessage(f'错误: {error_msg}')
        logging.error(error_msg)
        self.log_text.append(f"错误: {error_msg}")

    def refresh_ports(self):
        """刷新并更新可用串口列表"""
        self.interface_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if ports:
            self.interface_combo.addItems(ports)
            logging.info(f"发现可用串口: {', '.join(ports)}")
        else:
            logging.warning("未发现可用串口")
            self.interface_combo.addItem("未发现串口")

def main():
    app = QApplication(sys.argv)
    window = CANMonitorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()