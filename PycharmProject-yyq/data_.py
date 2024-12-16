import csv
import os

# 定义一个函数，用于解析十六进制的 data 字段
def parse_can_data(data_str):
    # 将十六进制字符串分割为字节列表
    bytes_list = data_str.split()
    # 返回解析结果，包括原始字节、整数和可见 ASCII 字符
    return {
        "raw_bytes": bytes_list,
        "integers": [int(byte, 16) for byte in bytes_list],
        "ascii": ''.join(chr(int(byte, 16)) for byte in bytes_list if 32 <= int(byte, 16) <= 126),
    }

# 定义一个函数，尝试解读 CAN 数据
def interpret_data(data):
    try:
        raw_bytes = data['Parsed Data']['raw_bytes']
        # 示例解析逻辑（可根据协议修改）：
        # 假设前两个字节是设备状态
        mode = raw_bytes[0]
        flags = raw_bytes[1]
        # 假设第3-4字节为16位传感器值
        sensor_value = int(raw_bytes[2] + raw_bytes[3], 16)
        # 剩余字节可能是其他信息
        other_data = raw_bytes[4:]
        return f"Mode: {mode}, Flags: {flags}, Sensor Value: {sensor_value}, Other Data: {' '.join(other_data)}"
    except Exception as e:
        return f"Error interpreting data: {e}"

# 读取并处理 CSV 文件
def process_can_csv(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        processed_data = []
        for row in reader:
            cobid = int(row['cobid'], 16)  # 将 COB-ID 转为十六进制整数
            data_parsed = parse_can_data(row['data'])
            processed_data.append({
                "No.": int(row['No.']),
                "Timestamp(ms)": float(row['ms']),
                "TR": row['TR'],
                "RTR": row['rtr'],
                "COB-ID": f"0x{cobid:X}",  # 显示为16进制格式
                "Length": int(row['len']),
                "Parsed Data": data_parsed
            })
        return processed_data

# 打印解析后的数据
def display_processed_data(processed_data):
    for entry in processed_data:
        print(f"Message {entry['No.']}:")
        print(f"  Timestamp: {entry['Timestamp(ms)']} ms")
        print(f"  COB-ID: {entry['COB-ID']}")
        print(f"  Length: {entry['Length']}")
        print(f"  Raw Data: {' '.join(entry['Parsed Data']['raw_bytes'])}")
        print(f"  Integers: {entry['Parsed Data']['integers']}")
        print(f"  ASCII (if applicable): {entry['Parsed Data']['ascii']}")
        print(f"  Interpretation: {interpret_data(entry)}")
        print()

# 主程序
if __name__ == "__main__":
    file_path = r"D:\VScode_project\python\PycharmProject-yyq\20241121133452.csv"  # 替换为你的文件路径
    try:
        processed_data = process_can_csv(file_path)
        display_processed_data(processed_data)
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")
