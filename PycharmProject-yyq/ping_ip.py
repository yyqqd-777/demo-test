import subprocess
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def ping_host(ip):
    """Ping the specified IP address and return the output."""
    try:
        output = subprocess.check_output(["ping", "-n", "4", ip], encoding='gbk')  # Windows 下使用 gbk 编码
        return output
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output}"


def analyze_ping_result(output):
    """Analyze the ping result and return response times."""
    response_times = []
    lines = output.splitlines()

    for line in lines:
        if "时间=" in line:  # 找到时间响应的行
            # 提取时间值
            start_index = line.find("时间=") + len("时间=")
            end_index = line.find("ms", start_index)
            response_time = int(line[start_index:end_index])  # 转换为整数
            response_times.append(response_time)

    return response_times


# Global variables to store data
ip_addresses = ["10.0.64.233", "10.0.64.11", "10.0.64.46"]
response_time_lists = [[] for _ in ip_addresses]


def update(frame):
    """Update function for FuncAnimation."""
    for idx, ip_address in enumerate(ip_addresses):
        print(f"Pinging {ip_address}...")
        ping_result = ping_host(ip_address)
        print(f"Ping Result for {ip_address}:\n{ping_result}")

        response_times = analyze_ping_result(ping_result)
        response_time_lists[idx].extend(response_times)  # 将响应时间添加到对应的列表中

    plt.clf()  # 清除当前的图形
    for i, ip in enumerate(ip_addresses):
        plt.plot(response_time_lists[i], label=ip)

    plt.title("Ping Response Times")
    plt.xlabel("Ping Count")
    plt.ylabel("Response Time (ms)")
    plt.legend()
    plt.grid()


if __name__ == "__main__":
    # 创建图形
    plt.figure()
    ani = FuncAnimation(plt.gcf(), update, interval=5000)  # 每5秒更新一次

    plt.show()  # 开始动画循环
