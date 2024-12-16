class Robot(object):
    """
    机器人类，用于保存机器人的状态
    """
    state_update_flag = False
    state = "None"

    def __init__(self, robot_type, robot_label):
        self.robot_type = robot_type
        self.robot_label = robot_label

    def __str__(self) -> str:
        print(self.robot_label, self.robot_type, self.state)
        return "type: {:<7} id: {:<5} state: {:<15}".format(
            self.robot_type, self.robot_label, self.state
        )

    def update_state(self, payload):
        self.state = payload["mainState"]


class Ant(Robot):
    """
    蚂蚁机器人类
    """

    def __init__(self, robot_label, drop_height=0, lift_height=100):
        super().__init__("ANT", robot_label)
        self.height = self.drop_height = drop_height
        self.lift_height = lift_height

    def __str__(self) -> str:
        return (
            "type: {:<7} id: {:<5} state: {:<15} pos_x: {:<7} pos_y: {:<7} orientation: {:<5} lift_height: {:<5} scan: {:<5} battery: {:<3}%".format(
                self.robot_type,
                self.robot_label,
                self.state,
                self.position_x,
                self.position_y,
                self.orientation,
                self.height,
                self.scan_state,
                self.battery
            )
        )

    def is_lifted(self):
        return abs(self.height - self.lift_height) < 5

    def is_dropped(self):
        return abs(self.height - self.drop_height) < 5

    def update_state(self, payload):
        self.state = payload["mainState"]
        self.position_x = payload["coordX"]
        self.position_y = payload["coordY"]
        self.orientation = payload["orientation"]
        self.scan_state = payload["qrCodeStatus"]
        self.height = payload["liftHeight"]
        self.battery = payload["batPct"]


class Mole(Robot):
    """
    鼹鼠机器人类
    """

    load_state = 2  # 装载状态，0：未装载，1：已装载，2：未知状态

    def __init__(self, robot_label):
        super().__init__("MOLE", robot_label)

    def is_loaded(self):
        return self.load_state == 1

    def is_empty(self):
        return self.load_state == 0

    def update_state(self, state, loaded):
        self.state = state
        self.load_state = loaded


class Spyder(Robot):
    """
    蜘蛛机器人类
    """
    position = 0
    load_state = "Unknown"
    scan_state = "Unknown"
    scan_x = scan_z = 0  # 机器人坐标

    def __init__(self, robot_label):
        super().__init__("SPYDER", robot_label)

    def __str__(self) -> str:
        return (
            "type: {:<7} id: {:<5} state: {:<15} position: {:<7} loaded: {:<10} scan: {:<5} data: {:<20} x: {:<7} z: {:<7}".format(
                self.robot_type,
                self.robot_label,
                self.state,
                self.position,
                self.load_state,
                self.scan_state,
                self.scan_data,
                self.scan_x,
                self.scan_z,
            )
        )

    def is_loaded(self):
        return self.load_state

    def is_scanned(self):
        return self.scan_state

    def update_state(self, payload):
        self.state = payload["mainState"]
        self.position = payload["coordZ"]
        self.load_state = payload["loaded"] if "loaded" in payload else "Unknown"
        self.scan_state = payload["scannerStatus"]["qrCodeStatus"]
        self.scan_data = payload["scannerStatus"]["scannerData"]
        self.scan_x = payload["scannerStatus"]["scannerCoordX"]
        self.scan_z = payload["scannerStatus"]["scannerCoordZ"]


class Ladder(Robot):
    """
    梯子机器人类
    """

    def __init__(self, robot_label):
        super().__init__("LADDER", robot_label)

    def __str__(self) -> str:
        return (
            "type: {:<7} id: {:<5} state: {:<15} position: {:<7}".format(
                self.robot_type,
                self.robot_label,
                self.state,
                self.position
            )
        )

    def update_state(self, payload):
        self.state = payload["mainState"]
        self.position = payload["coordX"]
