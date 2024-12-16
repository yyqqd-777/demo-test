import logging
import time
import canopen

logging.basicConfig(filename="newfile.log",
                    format='%(asctime)s %(message)s',
                    datefmt="%Y-%m-%dT%H:%M:%S",
                    filemode='w')
logger = logging.getLogger()


class DSR018Can:
    def __init__(self, can_network, node_id):

        self.mag_dict = {
            'compose_status_1.servo_err_code': 0,
            'compose_status_1.servo_cur_vol': 0,
            'compose_status_1.servo_curr_current': 0,
            'compose_status_1.servo_cur_temp': 0,
            'compose_status_2.servo_cur_pos': 0,
            'compose_status_2.servo_speed': 0,
            'compose_status_2.servo_torque': 0,
            'compose_status_2.servo_niuju': 0
        }

        self.motor_pos = 0  # 经过转换后的位置

        self.node = can_network.add_node(node_id, 'ds_r018.eds')
        self.node.sdo.RESPONSE_TIMEOUT = 1.5

    def set_tpdo(self):
        self.node.tpdo.read()

        # self.node.tpdo[2].clear()
        # self.node.tpdo[3].clear()
        # self.node.tpdo[2].add_variable(0x6100, 56)
        # self.node.tpdo[2].add_variable(0x6100, 57)
        # self.node.tpdo[2].add_variable(0x6100, 18)

        self.node.tpdo[3].trans_type = 255
        self.node.tpdo[3].event_timer = 1000
        self.node.tpdo[3].enabled = True

        self.node.tpdo[4].trans_type = 255
        self.node.tpdo[4].event_timer = 1000
        self.node.tpdo[4].enabled = True

        self.node.tpdo.save()
        self.node.tpdo[3].add_callback(self.tpdo3_callback)
        self.node.tpdo[4].add_callback(self.tpdo4_callback)

    def tpdo3_callback(self, message):
        for var in message:
            self.mag_dict[var.name] = var.raw

    def tpdo4_callback(self, message):
        for var in message:
            self.mag_dict[var.name] = var.raw

    def print_mag_dict(self):
        return self.mag_dict

    def set_motor_id(self, id):
        """set motor id

        Args:
            id (int): motor id
        """
        data = id.to_bytes(length=1, byteorder='little')
        self.node.sdo.download(0x6100, 5, data)

    def set_motor_bitrate(self, bitrate):
        """set motor bitrate

        Args:
            bitrate (int): 01=125K, 02=250K, 04=500K
        """
        data = bitrate.to_bytes(length=1, byteorder='little')
        self.node.sdo.download(0x6100, 30, data)

    def set_motor_pos_zero(self):
        """set motor position to zero
        """
        self.node.sdo.download(0x6100, 31, b'\x00')

    def get_motor_error(self):
        """获取电机错误

        Returns:
            int: error code:
                bit0: 电压异常
                bit1: 电流过流
                bit2: 温度保护
                bit3: 堵转保护
                bit4: 硬件错误

        """
        motor_error = self.mag_dict['compose_status_1.servo_err_code']

        error = motor_error & 0x01
        error += motor_error & 0x02
        error += motor_error & 0x04
        error += motor_error & 0x08
        error += motor_error & 0x10

        return error

    def get_motor_pos(self):
        """电机位置计算：
            PDO上报的位置范围：-1800~1800
            下发位置0，电机会运行到位置 -1800
            PDO上报的位置 + 1800 = 实际位置

        Returns:
            int: 实际位置
        """
        if self.mag_dict['compose_status_2.servo_cur_pos'] > 0x8000:
            self.motor_pos = self.mag_dict['compose_status_2.servo_cur_pos'] - 0x10000
        else:
            self.motor_pos = self.mag_dict['compose_status_2.servo_cur_pos']

        print(self.motor_pos)
        return self.motor_pos + 1800

    def motor_action(self, pos, time):
        _pos = pos.to_bytes(length=2, byteorder='little', signed=True)
        _time = time.to_bytes(length=2, byteorder='little')
        out = _pos + _time
        self.node.sdo.download(0x6101, 1, out)


if __name__ == "__main__":
    network = canopen.Network()
    network.connect(channel='COM3', bustype='slcan', bitrate=500000)
    # network.connect(channel='COM3', bustype='slcan', bitrate=125000)
    # motor = DSR018Can(network, 1)
    # motor.set_motor_id(6)
    # motor.set_motor_bitrate(4)
    # motor.set_motor_pos_zero()
    # motor.motor_action(1000, 200)
    # time.sleep(0.5)
    # motor.motor_action(2000, 200)
    #bitrate
    # list_1 = [1, 3, 6, 8]
    # list_2 = [2, 4, 5, 7]
    # for i in range(1, 9):
    #     motor = DSR018Can(network, i)
    #     if i in list_1:
    #         motor.set_motor_bitrate(4)
    #     if i in list_2:
    #         motor.set_motor_bitrate(4)

    #zero 1
    # list_1 = [1, 3, 6, 8]
    # list_2 = [2, 4, 5, 7]
    # for i in range(1, 9):
    #     motor = DSR018Can(network, i)
    #     if i in list_1:
    #         motor.set_motor_pos_zero()
        # if i in list_2:
        #     motor.set_motor_pos_zero()

    # zero 2
    # list_1 = [1, 3]
    # list_1 = [2, 4]
    # list_1 = [6, 8]
    # list_1 = [5, 7]
    # for i in range(1, 9):
    #     motor = DSR018Can(network, i)
    #     if i in list_1:
    #         motor.set_motor_pos_zero()

    # motor.set_motor_pos_zero()

    # #move 1
    # list_1 = [1, 6]
    # list_2 = [3, 8]
    # for i in range(1, 9):
    #     motor = DSR018Can(network, i)
    #     if i in list_1:
    #         motor.motor_action(3100, 200)  # 1 4 6 7
    #         time.sleep(0.5)
    #         motor.motor_action(2100, 200)
    #     if i in list_2:
    #         motor.motor_action(1000, 200)  #200
    #         time.sleep(0.5)
    #         motor.motor_action(2000, 200)

    # move 2
    # list_1 = [4, 7]
    # list_2 = [2, 5]
    # for i in range(1, 9):
    #     motor = DSR018Can(network, i)
    #     if i in list_1:
    #         motor.motor_action(3100, 200)  # 1 4 6 7
    #         time.sleep(0.5)
    #         motor.motor_action(2100, 200)
    #     if i in list_2:
    #         motor.motor_action(1000, 200)  #
    #         time.sleep(0.5)
    #         motor.motor_action(2000, 200)

    #can2 move
    list_1 = [1, 4, 6, 7]
    list_2 = [2, 3, 5, 8]
    for i in range(1, 9):
        print(i)
        motor = DSR018Can(network, i)
        if i in list_1:
            motor.motor_action(3100, 200)  # 1 4 6 7
            time.sleep(0.5)
            motor.motor_action(2100, 200)
        if i in list_2:
            motor.motor_action(1000, 200)  #
            time.sleep(0.5)
            motor.motor_action(2000, 200)

    # load/unload
    # list_1 = [1, 4, 6, 7]
    # list_2 = [2, 3, 5, 8]
    # for i in range(1, 9):
    #     print(i)
    #     motor = DSR018Can(network, i)
    #     if i in list_1:
    #         motor.motor_action(3100, 200)  # 1 4 6 7
    #         time.sleep(0.5)
    #         motor.motor_action(2100, 200)
    #     if i in list_2:
    #         motor.motor_action(1000, 200)  # 2 3 5 8
    #         time.sleep(0.5)
    #         motor.motor_action(2000, 200)

    # motor.motor_action(1000, 200)
    # time.sleep(0.5)
    # motor.motor_action(2000, 200)
    # while True:
    # motor.motor_action(3100, 200) # 1 4 6 7
    # time.sleep(0.5)
    # motor.motor_action(2100, 200)
    # time.sleep(0.5)

    # list_1 = [ 5, 8]
    # list_2 = [ 6, 7]
    # for i in range(1, 9):
    #     motor = DSR018Can(network, i)
    #     if i in list_1:
    #         motor.motor_action(3100, 200)  # 1 4 5 8
    #         time.sleep(0.5)
    #         motor.motor_action(2100, 200)
    #     if i in list_2:
    #         motor.motor_action(1000, 200)  # 2 3 6 7
    #         time.sleep(0.5)
    #         motor.motor_action(2000, 200)

    # motor1 2100 3100
    # motor2 2000 1000
    # motor3 2000 1000
    # motor4 2100 3100
    # motor5 2100 3100
    # motor6 2000 1000
    # motor7 2000 1000
    # motor8 2100 3100
