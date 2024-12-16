import canopen

def receive_pdo_messages(channel, interface):
    try:
        # 创建CAN总线实例
        network = canopen.Network()
        network.connect(channel=channel, interface=interface, bitrate=1000000)
        print(f"Connected to CAN bus on {channel} using {interface}")

        # 添加远程节点
        node_id = 126 # 根据您的设备配置调整节点ID
        node = canopen.RemoteNode(node_id, 'flowservo_20240131.eds')  # 替换为实际的EDS文件路径
        network.add_node(node)

        # 启动CANopen节点
        node.nmt.state = 'OPERATIONAL'
        print("Node is operational")

        # 打印接收到的PDO数据的回调函数
        def pdo_callback(event):
            pdo = event["pdo"]
            print(f"Received PDO message: ID={pdo.cob_id:X}, Data={pdo.data.hex().upper()}")

        # 订阅所有PDO消息
        for pdo_mapping in node.pdo.values():
            pdo_mapping.add_callback(pdo_callback)

        # 持续监听CANopen网络
        print("Listening for PDO messages... Press Ctrl+C to exit")
        while True:
            network.check()

    except KeyboardInterrupt:
        print("Interrupted by user")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # 断开CANopen网络连接
        try:
            # 取消所有PDO订阅
            for pdo_mapping in node.pdo.values():
                pdo_mapping.remove_callback(pdo_callback)
        except Exception as e:
            print(f"Error while unsubscribing: {e}")

        network.disconnect()
        print("Disconnected from CAN bus")

if __name__ == "__main__":
    # 指定CAN通道和接口（根据实际情况调整）
    can_channel = 'COM14'  # Windows 上的COM端口
    can_interface = 'slcan'  # 使用SLCAN接口

    receive_pdo_messages(can_channel, can_interface)



# import canopen
#
# # 定义CAN接口和通道
# can_interface = 'slcan'  # 根据实际情况调整
# channel = 'COM14'  # 根据实际情况调整
#
# # 创建CANopen网络并连接到设备
# network = canopen.Network()
#
# try:
#     print("Connecting to CAN network...")
#     network.connect(channel=channel, interface=can_interface, bitrate=1000000)
#     print("Connected to CAN network")
#
#     # 添加节点
#     node_id = 126  # 根据您的设备配置调整节点ID
#     node = canopen.RemoteNode(node_id, 'flowservo_20240131.eds')  # 替换为实际的EDS文件路径
#     network.add_node(node)
#
#     # 检查网络和节点连接状态
#     if network.bus is None:
#         raise RuntimeError("Failed to connect to CAN network. Check your interface and channel settings.")
#
#     # 启动CANopen节点
#     print("Setting NMT state to OPERATIONAL...")
#     node.nmt.state = 'OPERATIONAL'
#     print("NMT state set to OPERATIONAL")
#
#     # 打印接收到的PDO数据的回调函数
#     def pdo_callback(msg, arbitration_id):
#         print(f"Received message: ID={arbitration_id:03X}, Data={msg.data.hex().upper()}")
#
#     # 订阅所有CAN消息
#     for can_id in range(0x000, 0x800):
#         network.subscribe(can_id, pdo_callback)
#
#     # 持续监听CANopen网络
#     print("Starting to listen for CAN messages...")
#     while True:
#         network.check()
#
# except canopen.SdoAbortedError as e:
#     print(f"SDO communication failed: {e}")
# except Exception as e:
#     print(f"An error occurred: {e}")
# finally:
#     # 断开CANopen网络连接
#     print("Disconnecting from CAN network...")
#     try:
#         # 取消所有订阅
#         for can_id in range(0x000, 0x800):
#             network.unsubscribe(can_id)
#     except Exception as e:
#         print(f"Error while unsubscribing: {e}")
#
#     network.disconnect()
#     print("Disconnected from CAN network")
