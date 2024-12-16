import json
import subprocess
import sys
from datetime import datetime

from LogTool import LogTool

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("paho-mqtt not found, installing...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "paho-mqtt"])
finally:
    import paho.mqtt.client as mqtt


class MQTTMsg:
    def __init__(self, topic, payload):
        super().__init__()
        self.topic = topic
        if isinstance(payload, str):
            payload = json.dumps(json.loads(payload), indent=4)
        self.payload = payload

    def __str__(self):
        return f"MQTTMessage(topic={self.topic}, payload={self.payload})"

    def __repr__(self):
        return f"MQTTMessage(topic={self.topic}, payload={self.payload})"


def build_ladder_move_command(
        robot_label: str,
        set_id: str,
        command_id: str | int,
        init_position: int,
        target_position: int,
        vel: int,
        acc: int
):
    return {
        "robotCommandLabel": f"{robot_label}-{set_id}-{command_id}",
        "commandContent": {
            "robotCommandType": "MOVE",
            "coordX": target_position,
            "maxVelocity": vel,
            "maxAcceleration": acc,
        },
        "expectedState": {
            "coordX": init_position,
            "xTolerance": 10,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 50,
        },
        "futureState": {
            "coordX": target_position,
            "xTolerance": 10,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 50,
        },
    }


def build_ladder_move_command_set(robot_label: str, init_pos: int, command_param: list):
    topic = f"robot/commandSet/create/{robot_label}"
    set_id = f"SET-{datetime.now().isoformat()}"

    commands = []
    for command_id, (target_pos, vel, acc) in enumerate(command_param):
        commands.append(build_ladder_move_command(
            robot_label, set_id, str(command_id + 1), init_pos, target_pos, vel, acc))
        init_pos = target_pos

    payload = {
        "robotCommandSetLabel": f"{robot_label}-{set_id}",
        "timestamp": datetime.now().isoformat(),
        "robotCommands": commands,
    }
    return MQTTMsg(topic, payload)


def build_ladder_home_command_set(
        robot_label: str,
        command_type: str,
        distance_between_dm_codes: int = 0,
        origin_offset: int = 0
):
    topic = f"robot/commandSet/create/{robot_label}"
    set_id = f"SET-{datetime.now().isoformat()}"

    commands = [
        {
            "robotCommandLabel": f"{robot_label}-{set_id}-0",
            "commandContent": {
                "robotCommandType": command_type,
                "distanceBetweenDmCodes": distance_between_dm_codes,
                "originOffset": origin_offset
            },
            "expectedState": {
                "coordX": 0,
                "xTolerance": 10,
                "velocity": 0,
                "velocityTolerance": 50,
                "acceleration": 0,
                "accelerationTolerance": 50
            },
            "futureState": {
                "coordX": 0,
                "xTolerance": 10,
                "velocity": 0,
                "velocityTolerance": 50,
                "acceleration": 0,
                "accelerationTolerance": 50
            }
        }
    ]

    payload = {
        "robotCommandSetLabel": f"{robot_label}-{set_id}",
        "timestamp": datetime.now().isoformat(),
        "robotCommands": commands,
    }
    return MQTTMsg(topic, payload)


def build_spyder_move_command(
        robot_label: str,
        set_id: str,
        command_id: str | int,
        init_position: int,
        target_position: int,
        vel: int,
        acc: int,
        load_sensor_front: bool = False,
        load_sensor_rear: bool = False
):
    return {
        "robotCommandLabel": f"{robot_label}-{set_id}-{command_id}",
        "commandContent": {
            "robotCommandType": "MOVE",
            "coordZ": target_position,
            "maxVelocity": vel,
            "maxAcceleration": acc,
        },
        "expectedState": {
            "coordZ": init_position,
            "zTolerance": 10,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 50,
            "loadSensorFront": load_sensor_front,
            "loadSensorRear": load_sensor_rear,
            "antipinchSensorFront": False,
            "antipinchSensorRear": False,
        },
        "futureState": {
            "coordZ": target_position,
            "zTolerance": 10,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 50,
            "loadSensorFront": load_sensor_front,
            "loadSensorRear": load_sensor_rear,
            "antipinchSensorFront": False,
            "antipinchSensorRear": False,
        }
    }


def build_spyder_move_command_set(robot_label: str, init_pos: int, command_param: list, load_sensor_front: bool = False, load_sensor_rear: bool = False):
    topic = f"robot/commandSet/create/{robot_label}"
    set_id = f"SET-{datetime.now().isoformat()}"

    commands = []
    for command_id, (target_pos, vel, acc) in enumerate(command_param):
        commands.append(build_spyder_move_command(
            robot_label, set_id, str(command_id + 1), init_pos, target_pos, vel, acc, load_sensor_front, load_sensor_rear))
        init_pos = target_pos

    payload = {
        "robotCommandSetLabel": f"{robot_label}-{set_id}",
        "timestamp": datetime.now().isoformat(),
        "robotCommands": commands,
    }
    return MQTTMsg(topic, payload)


def build_spyder_action_command_set(robot_label: str, init_pos: int, load: bool, forward: bool, distance: int):
    topic = f"robot/commandSet/create/{robot_label}"
    set_id = f"SET-{datetime.now().isoformat()}"

    commands = [{
        "robotCommandLabel": f"{robot_label}-{set_id}-0",
        "commandContent": {
            "robotCommandType": "LOAD" if load else "UNLOAD",
            "side": "FORWARD" if forward else "BACKWARD",
            "distance": distance,
        },
        "expectedState": {
            "coordZ": init_pos,
            "zTolerance": 10,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 50,
            "loadSensorFront": True if not load else False,
            "loadSensorRear": True if not load else False,
            "antipinchSensorFront": False,
            "antipinchSensorRear": False,
        },
        "futureState": {
            "coordZ": init_pos,
            "zTolerance": 10,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 50,
            "loadSensorFront": True if load else False,
            "loadSensorRear": True if load else False,
            "antipinchSensorFront": False,
            "antipinchSensorRear": False,
        }
    }]

    payload = {
        "robotCommandSetLabel": f"{robot_label}-{set_id}",
        "timestamp": datetime.now().isoformat(),
        "robotCommands": commands,
    }
    return MQTTMsg(topic, payload)


def build_spyder_home_command_set(
        robot_label: str,
        command_type: str,
        distance_to_dm_codes: int = 200,
        origin_offset: int = 200
):
    topic = f"robot/commandSet/create/{robot_label}"
    set_id = f"SET-{datetime.now().isoformat()}"

    commands = [
        {
            "robotCommandLabel": f"{robot_label}-{set_id}-0",
            "commandContent": {
                "robotCommandType": command_type,
                "distanceToDmCodes": distance_to_dm_codes,
                "originOffset": origin_offset
            },
            "expectedState": {
                "coordZ": 0,
                "zTolerance": 10,
                "velocity": 0,
                "velocityTolerance": 50,
                "acceleration": 0,
                "accelerationTolerance": 50,
                "loadSensorFront": False,
                "loadSensorRear": False,
                "antipinchSensorFront": False,
                "antipinchSensorRear": False,
            },
            "futureState": {
                "coordZ": 0,
                "zTolerance": 10,
                "velocity": 0,
                "velocityTolerance": 50,
                "acceleration": 0,
                "accelerationTolerance": 50,
                "loadSensorFront": False,
                "loadSensorRear": False,
                "antipinchSensorFront": False,
                "antipinchSensorRear": False,
            }
        }
    ]

    payload = {
        "robotCommandSetLabel": f"{robot_label}-{set_id}",
        "timestamp": datetime.now().isoformat(),
        "robotCommands": commands,
    }
    return MQTTMsg(topic, payload)


def build_ant_action_command(
        robot_label: str,
        set_id: str,
        command_id: str | int,
        command_type: str,
        init_x: int,
        init_y: int,
        init_ori: int,
        init_lift: int,
        target_x: int,
        target_y: int,
        target_ori: int,
        target_lift: int,
        vel: int,
        acc: int
):
    return {
        "robotCommandLabel": f"{robot_label}-{set_id}-{command_id}",
        "commandContent": {
            "robotCommandType": command_type,
            "coordX": target_x,
            "coordY": target_y,
            "coordZ": 0,
            "finalTargetX": target_x,
            "finalTargetY": target_y,
            "finalTargetZ": 0,
            "maxVelocity": vel,
            "maxAcceleration": acc,
            "orientation": int(target_ori * 100),
            "liftHeight": target_lift,
        },
        "expectedState": {
            "coordX": init_x,
            "coordY": init_y,
            "coordZ": 0,
            "xTolerance": 50,
            "yTolerance": 50,
            "zTolerance": 50,
            "orientation": int(init_ori * 100),
            "orientationTolerance": 1000,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 100,
            "angularVelocity": 0,
            "angularVelocityTolerance": 100,
            "angularAcceleration": 0,
            "angularAccelerationTolerance": 100,
            "liftHeight": init_lift,
            "liftHeightTolerance": 100,
            "loadSensor": False
        },
        "futureState": {
            "coordX": target_x,
            "coordY": target_y,
            "coordZ": 0,
            "xTolerance": 50,
            "yTolerance": 50,
            "zTolerance": 50,
            "orientation": int(target_ori * 100),
            "orientationTolerance": 1000,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 100,
            "angularVelocity": 0,
            "angularVelocityTolerance": 100,
            "angularAcceleration": 0,
            "angularAccelerationTolerance": 100,
            "liftHeight": target_lift,
            "liftHeightTolerance": 100,
            "loadSensor": False
        }
    }


def build_ant_action_command_set(robot_label: str, init_pos: tuple, command_param: list):
    topic = f"robot/commandSet/create/{robot_label}"
    set_id = f"SET-{datetime.now().isoformat()}"

    curr_state = {
        'x': init_pos[0],
        'y': init_pos[1],
        'ori': init_pos[2],
        'lift': init_pos[3]
    }

    commands = []
    for command_id, params in enumerate(command_param):
        target_state = curr_state.copy()
        vel = acc = 0
        command_type = params[0]
        if command_type == 'MOVE':
            target_state['x'] = params[1]
            target_state['y'] = params[2]
            vel = params[3]
            acc = params[4]
        elif command_type == 'SPIN':
            target_state['ori'] = params[1]
        elif command_type == 'LIFT':
            target_state['lift'] = params[1]
        command = build_ant_action_command(
            robot_label,
            set_id,
            command_id,
            command_type,
            curr_state['x'],
            curr_state['y'],
            curr_state["ori"],
            curr_state['lift'],
            target_state["x"],
            target_state["y"],
            target_state['ori'],
            target_state["lift"],
            vel,
            acc)
        commands.append(command)
        curr_state = target_state

    payload = {
        "robotCommandSetLabel": f"{robot_label}-{set_id}",
        "timestamp": datetime.now().isoformat(),
        "robotCommands": commands,
    }
    return MQTTMsg(topic, payload)


def build_robot_command(robot_label: str, set_id: str, command_type: str, command_id: str | int = 0):
    return {
        "robotCommandLabel": f"{robot_label}-{set_id}-{command_id}",
        "commandContent": {
            "robotCommandType": command_type
        },
        "expectedState": {
            "coordX": 0,
            "coordY": 0,
            "coordZ": 0,
            "xTolerance": 10,
            "yTolerance": 10,
            "zTolerance": 10,
            "orientation": 0,
            "orientationTolerance": 200,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 100,
            "angularVelocity": 0,
            "angularVelocityTolerance": 100,
            "angularAcceleration": 0,
            "angularAccelerationTolerance": 100,
            "liftHeight": 0,
            "liftHeightTolerance": 100,
            "loadSensor": False,
            "loadSensorFront": False,
            "loadSensorRear": False,
            "antipinchSensorFront": False,
            "antipinchSensorRear": False,
        },
        "futureState": {
            "coordX": 0,
            "coordY": 0,
            "coordZ": 0,
            "xTolerance": 10,
            "yTolerance": 10,
            "zTolerance": 10,
            "orientation": 0,
            "orientationTolerance": 200,
            "velocity": 0,
            "velocityTolerance": 50,
            "acceleration": 0,
            "accelerationTolerance": 100,
            "angularVelocity": 0,
            "angularVelocityTolerance": 100,
            "angularAcceleration": 0,
            "angularAccelerationTolerance": 100,
            "liftHeight": 0,
            "liftHeightTolerance": 100,
            "loadSensor": False,
            "loadSensorFront": False,
            "loadSensorRear": False,
            "antipinchSensorFront": False,
            "antipinchSensorRear": False,
        }
    }


def build_robot_command_set(robot_label: str, command_type: str):
    topic = f"robot/commandSet/create/{robot_label}"
    set_id = f"SET-{datetime.now().isoformat()}"

    commands = [build_robot_command(robot_label, set_id, command_type)]
    payload = {
        "robotCommandSetLabel": f"{robot_label}-{set_id}",
        "timestamp": datetime.now().isoformat(),
        "robotCommands": commands,
    }
    return MQTTMsg(topic, payload)


class MQTTClient:
    __on_receive_callback = None

    def __init__(
            self,
            client_id="paho-mqtt",
            callback=None
    ):
        # generate a unique client ID = client_id + current time
        self.client_id = client_id + "-" + str(datetime.now().isoformat())
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id,
        )
        self.__on_receive_callback = callback
        self.log = LogTool("mqtt", "mqtt.log").get_logger()

    def __on_connect(self, client, dummy, userdata, flags, rc):
        """
        mqttc.on_connect is an instance method.
        It implicitly passes the instance as the first argument to the method (usually known as self)
        However, the callback function is inside the class, so
            the first argument is the instance itself,
            the second argument will be the client,
            the third argument will be None.
        """
        pass

    def __on_message(self, client, userdata, msg):
        message = MQTTMsg(topic=msg.topic, payload=msg.payload.decode("utf-8"))
        self.log.info(f"接收 <- {message}")
        if self.__on_receive_callback:
            self.__on_receive_callback(message)

    def start(self, host="localhost", port=1883, username='', password=''):
        self.client.on_connect = self.__on_connect  # bind function to callback
        self.client.on_message = self.__on_message
        self.client.username_pw_set(username, password)
        self.client.connect(host, port)  # connect to broker
        self.client.loop_start()  # start loop to process received messages
        self.log.info(f"MQTT客户端: {self.client_id} 已启动")

    def stop(self):
        self.client.disconnect()
        self.client.loop_stop()
        self.log.info(f"MQTT客户端: {self.client_id} 已关闭")

    def subscribe(self, topic, qos=2):
        self.client.subscribe(topic, qos)

    def publish(self, robot_label="", topic="", payload=None, qos=2, retain=False):
        if payload is None:
            payload = {}
        if not topic:
            topic = "robot/commandSet/create/" + robot_label
        if isinstance(payload, dict):
            payload = json.dumps(payload, indent=2)
        self.client.publish(topic, str(payload), qos, retain)
        self.log.info(f"发送 -> {MQTTMsg(topic=topic, payload=payload)}")

    def add_robot(self, robot_label):
        self.subscribe(f"robot/state/{robot_label}")
        self.subscribe(f"robot/command/status/{robot_label}")
        self.subscribe(f"robot/commandSet/create/{robot_label}")
