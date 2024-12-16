import time
import canopen
import logging
from canopen import SdoCommunicationError

# Create and configure logger
logging.basicConfig(filename="/home/orangepi/canopennode_test/newfile.log",
                    format='%(asctime)s %(message)s',
                    datefmt="%Y-%m-%dT%H:%M:%S",
                    filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

path = '/home/orangepi/eds_file/flowservo.eds'
network = canopen.Network()
network.connect(channel='can0', bustype='socketcan')
can0_node = network.add_node(node=80, object_dictionary=path)

can0_node.RESPONSE_TIMEOUT = 1.5

if __name__ == '__main__':
    count = 0

    try:
        while True:
            try:
                device_type_data = can0_node.sdo.upload(0x1001, 0)
                time.sleep(1)
                can0_node.sdo.download(0x1007, 0, b'\x00\x00\x00\x00')
                time.sleep(1)
                print(f"This is the subloop {count + 1}")
                logger.warning(f"This is the subloop {count + 1}")
                count += 1
            except SdoCommunicationError:
                time.sleep(1)
                print("Sdo Communication Error")
                logger.warning("Sdo Communication Error")

    except KeyboardInterrupt:
        pass

network.disconnect()
