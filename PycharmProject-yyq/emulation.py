# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class Simulator:
    # ... 其余代码保持不变 ...
    def __init__(self):
        # 初始化模拟器状态
        self.running = False
        self.current_time = 0
        self.events = []
        self.components = {}
    
    def add_component(self, name, component):
        """添加组件到模拟器"""
        self.components[name] = component
    
    def schedule_event(self, time, event):
        """安排事件"""
        self.events.append((time, event))
        self.events.sort(key=lambda x: x[0])  # 按时间排序
    
    def run(self, duration):
        """运行模拟器"""
        self.running = True
        self.current_time = 0
        
        while self.running and self.current_time < duration:
            # 处理当前时间的所有事件
            while self.events and self.events[0][0] <= self.current_time:
                _, event = self.events.pop(0)
                self.process_event(event)
            
            # 更新所有组件状态
            self.update_components()
            
            self.current_time += 1
    
    def process_event(self, event):
        """处理事件"""
        print(f"处理事件: {event} 在时间 {self.current_time}")
    
    def update_components(self):
        """更新所有组件状态"""
        for component in self.components.values():
            component.update(self.current_time)

class Component:
    def __init__(self, name):
        self.name = name
        self.state = None
    
    def update(self, time):
        """更新组件状态"""
        pass

# 使用示例
def main():
    # 创建模拟器实例
    sim = Simulator()
    
    # 创建并添加组件
    comp1 = Component("组件1")
    sim.add_component("comp1", comp1)
    
    # 安排一些事件
    sim.schedule_event(5, "事件1")
    sim.schedule_event(10, "事件2")
    
    # 运行模拟
    sim.run(duration=20)

if __name__ == "__main__":
    main()