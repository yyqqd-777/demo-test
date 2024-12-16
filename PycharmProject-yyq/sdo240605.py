import time
import canopen
import logging
import struct

logging.basicConfig(level=logging.INFO)
# 初始化网络和连接节点

network = canopen.Network()
network.connect(channel='COM7', bustype='slcan', bitrate=1000000)
node1 = network.add_node(1, 'flowservo_20240131.eds')
node2 = network.add_node(2, 'flowservo_20240131.eds')

def target_position():
    try:
        node1.sdo.download(0x6060, 0, b'\x01')
        node2.sdo.download(0x6060, 0, b'\x01')
        logging.info("Set absolute position mode")
        time.sleep(0.1)

        node1.sdo.download(0x607A, 0, b'\x27\x50\x00\x00')
        node2.sdo.download(0x607A, 0, b'\x27\x50\x00\x00')

        # node2.sdo.download(0x6081, 0x00, struct.pack('H', 0x2750))
        logging.info("Set target position")
        time.sleep(0.1)

        node1.sdo.download(0x6081, 0, b'\x27\x70\x00\x00')
        node2.sdo.download(0x6081, 0, b'\x27\x70\x00\x00')

        logging.info("Set acceleration")
        time.sleep(0.1)
    except Exception as e:
        logging.error(f"Error in target_position: {e}")


def contorol():
    control_words = [
        b'\x80\x00',
        b'\x00\x00',
        b'\x06\x00',
        b'\x07\x00',
        b'\x0F\x00',
        b'\x2F\x00',
        b'\x3F\x00'
    ]

    try:
        for cw in control_words:
            node1.sdo.download(0x6040, 0, cw)
            node2.sdo.download(0x6040, 0, cw)
            logging.info(f"Sent control word: {cw}")
            time.sleep(0.1)
    except Exception as e:
        logging.error(f"Error in contorol: {e}")
    network.disconnect()

def run():
        target_position()
        contorol()

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        network.disconnect()