import canopen

class CanNetworkConfig:
    def __init__(self, can_interface="COM14", bitrate=1000000, nodes=None):
        self.can_interface = can_interface
        self.bitrate = bitrate
        self.nodes = nodes if nodes is not None else []

    def add_node(self, node_id, eds_file):
        self.nodes.append({"node_id": node_id, "eds_file": eds_file})

    def remove_node(self, node_id):
        self.nodes = [node for node in self.nodes if node["node_id"] != node_id]

def configure_can_network(config):
    """
    配置CANopen网络的连接信息。

    :param config: CanNetworkConfig 对象，包含CANopen网络的配置信息。
    :return: 配置后的CANopen网络对象。
    """
    # 创建CANopen网络对象
    network = canopen.Network()

    # 配置CAN接口
    network.connect(bustype='socketcan', channel=config.can_interface, bitrate=config.bitrate)
    print(f"已连接到 CAN 接口 {config.can_interface}，波特率 {config.bitrate}")

    # 配置节点
    for node_config in config.nodes:
        node_id = node_config["node_id"]
        eds_file = node_config["eds_file"]
        node = canopen.RemoteNode(node_id, eds_file)
        network.add_node(node)
        print(f"已添加节点 ID {node_id}，EDS 文件 {eds_file}")

    return network

# 使用示例
# 创建配置对象
config = CanNetworkConfig(
    can_interface="can0",
    bitrate=250000,
    nodes=[
        {"node_id": 1, "eds_file": "path/to/your/node1.eds"},
        {"node_id": 2, "eds_file": "path/to/your/node2.eds"}
    ]
)

# 添加新的节点
config.add_node(3, "path/to/your/node3.eds")

# 移除节点
config.remove_node(2)

# 配置并连接网络
network = configure_can_network(config)
if network:
    print("网络配置成功")
