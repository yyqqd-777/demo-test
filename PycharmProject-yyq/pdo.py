import time
import can
import canopen
import csv
from datetime import datetime
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def print_motor_msg(message):
    print(f'{message.name} received')
    for var in message:
        print(f'{var.name} = {var.raw}')


def initialize_canopen_network(network, node_id, eds_file):
    """初始化CANopen网络并配置TPDO"""
    # node = network.add_node(node_id, eds_file)
    # node.tpdo.read()
    # node.tpdo[1].add_callback(print_motor_msg)
    # return node

    node = network.add_node(node_id, eds_file)
    node.tpdo.read()

    # 配置TPDO1
    node.tpdo[1].clear()
    node.tpdo[1].add_variable(0x606C)  # 电机转速
    node.tpdo[1].add_variable(0x6077)  # 电机扭矩
    node.tpdo[1].trans_type = 255  # 周期性发送
    node.tpdo[1].event_timer = 1000  # 每1000ms发送一次
    node.tpdo[1].enabled = True

    # 切换到PRE-OPERATIONAL状态以进行配置
    node.nmt.state = 'PRE-OPERATIONAL'
    time.sleep(0.1)  # 等待状态切换

    # 保存TPDO配置
    node.tpdo.save()
    node.nmt.state = 'OPERATIONAL'

    node.tpdo[1].add_callback(print_motor_msg)
    return node

# def create_csv_file():
#     """创建CSV文件并写入标题行"""
#     filename = f"motor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
#     with open(filename, mode='w', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(["Timestamp", "Motor Speed", "Motor Torque"])
#     return filename
#
#
# def append_to_csv(filename, data):
#     """追加数据到CSV文件"""
#     with open(filename, mode='a', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(data)
#
#
# def print_and_save_motor_status(filename, pdo):
#     """处理接收到的TPDO消息，并保存到CSV文件"""
#     try:
#         logger.info('TPDO received')
#         data = [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
#         for var in pdo:
#             logger.info('%s = %d' % (var.name, var.raw))
#             data.append(var.raw)
#         append_to_csv(filename, data)
#     except Exception as e:
#         logger.error(f"Error processing TPDO message: {e}")


def main():
    channel = 'COM7'
    bustype = 'slcan'
    bitrate = 1000000
    eds_file = 'flowservo_20240131.eds'
    node_id = 126

    network = canopen.Network()
    network.connect(channel=channel, bustype=bustype, bitrate=bitrate)
    node1 = initialize_canopen_network(network, node_id, eds_file)
    # node2 = initialize_canopen_network(network, 2, eds_file)
    # node3 = initialize_canopen_network(network, 3, eds_file)

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            network.disconnect()
            logger.info("Starting main loop. Press Ctrl+C to exit.")
            logger.info("KeyboardInterrupt detected. Exiting...")
        # finally:
        #
        #     logger.info("Network disconnected.")


if __name__ == "__main__":
    main()
