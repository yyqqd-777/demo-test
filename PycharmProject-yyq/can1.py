import canopen
import logging
import time
import csv
from datetime import datetime

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_csv_file():
    """创建CSV文件并写入标题行"""
    filename = f"motor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Motor Speed", "Motor Torque"])
    return filename


def append_to_csv(filename, data):
    """追加数据到CSV文件"""
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


def print_and_save_motor_status(filename, pdo):
    """处理接收到的TPDO消息，并保存到CSV文件"""
    try:
        logger.info('TPDO received')
        data = [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        for var in pdo:
            logger.info('%s = %d' % (var.name, var.raw))
            data.append(var.raw)
        append_to_csv(filename, data)
    except Exception as e:
        logger.error(f"Error processing TPDO message: {e}")
def initialize_canopen_network(channel, bustype, bitrate, node_id, eds_file):
    """初始化CANopen网络并添加节点"""
    network = canopen.Network()
    network.connect(channel=channel, interface=bustype, bitrate=bitrate)
    node = network.add_node(node_id, eds_file)
    return network, node


def check_sdo_communication(node):
    """检查SDO通信是否正常"""
    try:
        # 切换到PRE-OPERATIONAL状态
        logger.info("Setting node to PRE-OPERATIONAL state")
        node.nmt.state = 'PRE-OPERATIONAL'
        time.sleep(0.1)  # 等待状态切换

        # 尝试读取设备类型（索引0x1000，子索引0x00）
        logger.info("Attempting to read device type (0x1000)")
        device_type = node.sdo[0x1000].raw
        logger.info(f"Device type: {device_type}")

        # 尝试读取控制字（索引0x6040，子索引0x00）
        logger.info("Attempting to read control word (0x6040)")
        control_word = node.sdo[0x6040].raw
        logger.info(f"Control word: {control_word}")

        logger.info("SDO communication is working properly.")
    except canopen.SdoCommunicationError as e:
        logger.error(f"SDO Communication Error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


def configure_tpdo(node):
    """配置TPDO"""
    try:
        # 读取当前TPDO配置
        node.tpdo.read()
        tpdo1 = node.tpdo[1]

        # 清除当前TPDO映射
        tpdo1.clear()

        # 逐个添加变量到TPDO映射，并进行调试
        try:
            tpdo1.add_variable('Error register')  # 例如：0x1001
            logger.info("Added 'Error register' to TPDO")
        except Exception as e:
            logger.error(f"Error adding 'Error register' to TPDO: {e}")


        try:
            tpdo1.add_variable('Digital inputs')  # 例如：0x60FD
            logger.info("Added 'Digital inputs' to TPDO")
        except Exception as e:
            logger.error(f"Error adding 'Digital inputs' to TPDO: {e}")

        # 设置传输类型和事件计时器
        tpdo1.trans_type = 1  # 传输类型
        tpdo1.event_timer = 1000  # 事件计时器：1000ms

        # 启用TPDO
        tpdo1.enabled = True
        tpdo1.save()

        logger.info(f"TPDO1 configured with variables: {tpdo1.map}")
    except Exception as e:
        logger.error(f"Error configuring TPDO: {e}")


def main():
    channel = 'COM14'
    bustype = 'slcan'
    bitrate = 1000000
    node_id = 126
    eds_file = 'flowservo_20240131.eds'

    network = None
    node = None
    try:
        network, node = initialize_canopen_network(channel, bustype, bitrate, node_id, eds_file)
        if network is None or node is None:
            logger.error("Failed to initialize CANopen network or node.")
            return

        # 检查SDO通信是否正常
        check_sdo_communication(node)

        # 配置TPDO
        configure_tpdo(node)

        # 切换到OPERATIONAL状态以开始正常运行
        node.nmt.state = 'OPERATIONAL'
        time.sleep(0.1)  # 等待状态切换

        # 添加回调函数处理TPDO消息
        node.tpdo[1].add_callback(lambda pdo: print_and_save_motor_status(filename, pdo))
        logger.info("Starting main loop. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt detected. Exiting...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        # 确保在退出时断开网络连接
        if network is not None:
            network.disconnect()
            logger.info("Network disconnected.")


if __name__ == "__main__":
    main()
