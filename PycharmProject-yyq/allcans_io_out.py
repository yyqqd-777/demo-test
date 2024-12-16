import canopen
import time

network = canopen.Network()
network.connect(channel='COM7', bustype='slcan',bitrate=1000000)

node = network.add_node(12, 'objdict.eds')
node.nmt.state = 'OPERATIONAL'
node.sdo.RESPONSE_TIMEOUT = 1

node.sdo.download(0x2005, 1)


network.disconnect()