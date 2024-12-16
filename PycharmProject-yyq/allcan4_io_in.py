import canopen
import time

network = canopen.Network()
network.connect(channel='COM7', bustype='slcan',bitrate=1000000)

node = network.add_node(11, 'ALLCAN4.eds')
node.nmt.state = 'OPERATIONAL'
node.sdo.RESPONSE_TIMEOUT = 1


# 读取对象字典中的一个对象
try:
    response = node.sdo.upload(0x6000, 1,)
    print("Object 0x6000, Subindex 1 value:", response)
except Exception as e:
    print("Error reading object 0x6000, Subindex 1:", e)


