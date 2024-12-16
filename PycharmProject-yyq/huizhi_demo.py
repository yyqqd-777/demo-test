import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pythonProjectplay import mqtt_s


# 定义变量类和消息类
class Variable:
    def __init__(self, name, raw):
        self.name = name
        self.raw = raw


class Message:
    def __init__(self, name, variables):
        self.name = name
        self.variables = variables

    def __iter__(self):
        return iter(self.variables)


# 初始化绘图
fig, (ax1, ax2) = plt.subplots(2, 1)
xdata, speed_data, torque_data = [], [], []
ln1, = ax1.plot([], [], 'ro-', animated=True, label='Speed')
ln2, = ax2.plot([], [], 'bo-', animated=True, label='Torque')


def init():
    ax1.set_xlim(0, 10)
    ax1.set_ylim(800, 1300)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Speed')
    ax1.set_title('Real-time Speed Data')
    ax1.legend()

    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 200)
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Torque')
    ax2.set_title('Real-time Torque Data')
    ax2.legend()

    return ln1, ln2
print(f"Received `{mqtt_s.data_dict}` from  mqtt.s")

def update(frame):
    xdata.append(frame)

    # 获取速度和扭矩数据
    speed = mqtt_s.data_dict.get('Speed', 0)
    torque = mqtt_s.data_dict.get('Torque', 0)

    speed_data.append(speed)
    torque_data.append(torque)
    # 更新图形数据
    ln1.set_data(xdata, speed_data)
    ln2.set_data(xdata, torque_data)

    # 更新x轴的显示范围
    ax1.set_xlim(max(0, frame - 10), frame + 1)
    ax2.set_xlim(max(0, frame - 10), frame + 1)

    # 确保y轴根据数据自动调整
    ax1.relim()
    ax1.autoscale_view()
    ax2.relim()
    ax2.autoscale_view()

    return ln1, ln2

ani = animation.FuncAnimation(fig, update, frames=range(100), init_func=init, blit=False, interval=1000)
plt.tight_layout()
plt.show()
