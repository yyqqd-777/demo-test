import canopen
from argparse import ArgumentParser


parser = ArgumentParser(description = 'ALL-CAN-R arguments')
parser.add_argument('can_interface', help = "COM3 or can0 or can1 ...", type = str)
parser.add_argument('can_bitrate', help = "can bitrate", type = int)
# parser.add_argument('new_bitrate', help = "new bitrate", type = int)
parser.add_argument('now_node_id', help = "ID of the current device", type = str)
parser.add_argument('new_node_id', help = "New ID of the device", type = str)

args = parser.parse_args()

network = canopen.Network()
network.connect(bustype='slcan', channel=args.can_interface, bitrate=args.can_bitrate)
node = network.add_node(int(args.now_node_id), 'objdict.eds')

def test_lss_sever(new_node):
    vendor_id = node.sdo[0x1018][1]
    product_code = node.sdo[0x1018][2]
    revision_version = node.sdo[0x1018][3]
    serial_number = node.sdo[0x1018][4]

    print("Vendor-ID str: ", vendor_id.get_data().decode('utf-8')[::-1])
    print("Vendor-ID int: ", vendor_id.raw)
    print("Product Code int: ", product_code.raw)
    print("Revision Version int: ", revision_version.raw)
    print("Serial Number int: ", serial_number.raw)

    ret_bool = network.lss.send_switch_state_selective(vendor_id.raw, product_code.raw, revision_version.raw, serial_number.raw)

    if ret_bool:
        network.lss.configure_node_id(new_node)
        network.lss.configure_bit_timing(0)
        # network.lss.set_baud_rate(args.new_bitrate)
        network.lss.store_configuration()
        network.lss.send_switch_state_global(network.lss.WAITING_STATE)

    node.nmt.state = 'RESET'

    node1 = network.add_node(new_node, 'objdict.eds')

    try:
        ret = node1.nmt.wait_for_heartbeat()
        print('Module status: ', ret)
        print('CAN Heartbeat Received')
    except:
        print('CAN Heartbeat Failed')

if __name__ == '__main__':
    test_lss_sever(int(args.new_node_id))
