import canopen
import time

network = canopen.Network()
network.connect(channel='COM3', bustype='slcan',bitrate=500000)
# network.connect(channel='COM3', bustype='slcan',bitrate=1000000)

node = network.add_node(14, 'ALLCAN4.eds')
# node = network.add_node(12, 'ALLCAN4.eds')
# node = network.add_node(13, 'ALLCAN4.eds')
# node = network.add_node(14, 'ALLCAN4.eds')
node.nmt.state = 'OPERATIONAL'
node.sdo.RESPONSE_TIMEOUT = 1

# node.sdo.download(0x6200, 1, bytes([0x01]))
# hex_array = [0x01, 0x02, 0x04, 0x08, 0x040, 0x02, 0x01]
# hex_array = [0x00, 0x03, 0x07, 0x0f]
hex_array = [0x0f, 0x07, 0x03, 0x00]
for i in (hex_array):
    node.sdo.download(0x6200, 1, bytes([i]))

    time.sleep(0.5)

network.disconnect()



