import csv
import os
import logging
from datetime import datetime
import struct

# 设置日志配置
logging.basicConfig(
    filename='motor_can_data.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

# 定义心流电机CAN ID
MOTOR_IDS = {
    0x701: "电机1",
    0x702: "电机2",
    0x703: "电机3",
    0x704: "电机4"
}

# 定义命令ID
CMD_IDS = {
    0x141: "读取电机状态1和错误标志",
    0x142: "读取电机状态2",
    0x143: "读取电机状态3",
    0x144: "电机控制指令"
}

def parse_motor_data(data_str, cobid):
    """根据心流电机协议解析数据"""
    bytes_list = data_str.split()
    # if len(bytes_list) < 8:
    #     return "数据长度不足"
        
    # 将字节列表转换为整数列表
    data_bytes = [int(byte, 16) for byte in bytes_list]
    
    # 根据不同的COB-ID解析数据
    if cobid in [0x141, 0x142, 0x143, 0x144]:
        # 解析电机状态数据
        motor_id = MOTOR_IDS.get(cobid, "未知电机")
        
        # 使用struct解包数据
        try:
            # 将字节数组打包成二进制数据
            data_binary = bytes(data_bytes)
            
            # 解析电机状态1数据 (示例)
            if cobid == 0x141:
                temperature = data_bytes[0]  # 温度
                voltage = struct.unpack('<H', data_binary[1:3])[0] / 10.0  # 电压
                error_code = data_bytes[3]  # 错误代码
                
                return {
                    "motor_id": motor_id,
                    "command": CMD_IDS[cobid],
                    "temperature": temperature,
                    "voltage": voltage,
                    "error_code": error_code,
                    "raw_data": ' '.join(bytes_list)
                }
                
            # 解析电机状态2数据
            elif cobid == 0x142:
                angle = struct.unpack('<H', data_binary[0:2])[0] / 10.0  # 角度
                speed = struct.unpack('<h', data_binary[2:4])[0]  # 速度
                torque = struct.unpack('<h', data_binary[4:6])[0] / 10.0  # 转矩
                
                return {
                    "motor_id": motor_id,
                    "command": CMD_IDS[cobid],
                    "angle": angle,
                    "speed": speed,
                    "torque": torque,
                    "raw_data": ' '.join(bytes_list)
                }
                
            # 解析电机状态3数据
            elif cobid == 0x143:
                position = struct.unpack('<l', data_binary[0:4])[0]  # 位置
                current = struct.unpack('<h', data_binary[4:6])[0] / 100.0  # 电流
                
                return {
                    "motor_id": motor_id,
                    "command": CMD_IDS[cobid],
                    "position": position,
                    "current": current,
                    "raw_data": ' '.join(bytes_list)
                }
                
        except Exception as e:
            return f"数据解析错误: {e}"
            
    return "未知的COB-ID"

def process_can_csv(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        processed_data = []
        for row in reader:
            cobid = int(row['cobid'], 16)
            parsed_data = parse_motor_data(row['data'], cobid)
            processed_data.append({
                "No.": int(row['No.']),
                "Timestamp(ms)": float(row['ms']),
                "TR": row['TR'],
                "RTR": row['rtr'],
                "COB-ID": f"0x{cobid:X}",
                "Length": int(row['len']),
                "Parsed Data": parsed_data
            })
        return processed_data

def log_processed_data(processed_data):
    for entry in processed_data:
        logging.info(f"Message {entry['No.']}")
        logging.info(f"  Timestamp: {entry['Timestamp(ms)']} ms")
        logging.info(f"  COB-ID: {entry['COB-ID']}")
        
        parsed_data = entry['Parsed Data']
        if isinstance(parsed_data, dict):
            logging.info(f"  电机ID: {parsed_data['motor_id']}")
            logging.info(f"  命令类型: {parsed_data['command']}")
            
            # 根据不同的命令类型记录不同的数据
            if '状态1' in parsed_data['command']:
                logging.info(f"  温度: {parsed_data['temperature']}°C")
                logging.info(f"  电压: {parsed_data['voltage']}V")
                logging.info(f"  错误代码: {parsed_data['error_code']}")
            elif '状态2' in parsed_data['command']:
                logging.info(f"  角度: {parsed_data['angle']}°")
                logging.info(f"  速度: {parsed_data['speed']}rpm")
                logging.info(f"  转矩: {parsed_data['torque']}Nm")
            elif '状态3' in parsed_data['command']:
                logging.info(f"  位置: {parsed_data['position']}")
                logging.info(f"  电流: {parsed_data['current']}A")
                
            logging.info(f"  原始数据: {parsed_data['raw_data']}")
        else:
            logging.info(f"  解析结果: {parsed_data}")
            
        logging.info("")  # 空行

if __name__ == "__main__":
    file_path = r"D:\VScode_project\python\PycharmProject-yyq\20241121133452.csv"
    try:
        logging.info("开始处理心流电机CAN数据文件")
        logging.info(f"文件路径: {file_path}")
        
        processed_data = process_can_csv(file_path)
        log_processed_data(processed_data)
        
        logging.info("CAN数据处理完成")
        
    except FileNotFoundError as e:
        logging.error(f"文件未找到: {e}")
    except Exception as e:
        logging.error(f"发生错误: {e}")