import time
import canopen
network = canopen.Network()
# network.connect(channel='COM3', bustype='slcan', bitrate=125000)
network.connect(channel='COM3', bustype='slcan', bitrate=500000)
# network.connect(channel='COM3', bustype='slcan', bitrate=1000000)
# network.scanner.search()
time.sleep(0.5)
for node_id in network.scanner.nodes:
    print("Found node %d!" % node_id)
network.disconnect()
