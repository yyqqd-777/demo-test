import can
import canopen
import time

# 配置你的 CAN 接口
CAN_INTERFACE = 'can0'  # 替换为你的 CAN 接口
FILENAME = 'data_log.txt'

# 定义回调函数
def on_tpdo_message(msg):
    # 假设速度在 msg.data 的第一个字节，扭矩在第二个字节
    speed = msg.data[0]  # 根据实际情况提取速度
    torque = msg.data[1]  # 根据实际情况提取扭矩
    for var in message:
        mag_dict[var.name] = var.raw
    # 将数据写入文件
    with open(FILENAME, 'a') as f:
        f.write(f"Speed: {speed}, Torque: {torque}\n")
    print(f"Logged - Speed: {speed}, Torque: {torque}")

def main():
    node_id = 1  # 替换为实际的节点 ID
    CAN_INTERFACE = 'can0'  # 替换为你的 CAN 接口名称

    network = canopen.Network()
    network.connect(channel=CAN_INTERFACE)

    # 订阅 TPDO
    node = network.add_node(node_id, 'ds_r018.eds')  # 替换为实际的 EDS 文件路径
    node.tpdo[0].callback = on_tpdo_message  # 确保定义了 on_tpdo_message 函数
    node.tpdo[0].start()

    try:
        while True:
            network.sync()  # 处理 CAN 消息
            time.sleep(0.1)  # 调整循环频率
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        network.disconnect()

if __name__ == "__main__":
    main()
