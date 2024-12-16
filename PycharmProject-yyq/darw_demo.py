import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import random

# 创建 Dash 应用
app = dash.Dash(__name__)

# 初始化数据存储
xdata = []
speed_data = []
torque_data = []

# 创建 Dash 布局
app.layout = html.Div([
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,
        n_intervals=0
    )
])

@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph(n):
    global xdata, speed_data, torque_data
    
    # 模拟获取数据
    speed = random.randint(800, 1300)
    torque = random.randint(0, 200)
    
    # 更新数据
    xdata.append(n)
    speed_data.append(speed)
    torque_data.append(torque)

    # 创建图形
    fig = go.Figure()
    
    # 添加数据线
    fig.add_trace(go.Scatter(x=xdata, y=speed_data, mode='lines+markers', name='Speed (mm/s)', marker=dict(color='red')))
    fig.add_trace(go.Scatter(x=xdata, y=torque_data, mode='lines+markers', name='Torque (Nm)', marker=dict(color='blue')))

    # 设置坐标轴标签
    fig.update_layout(
        xaxis_title='Time (seconds)',
        yaxis_title='Speed (mm/s) / Torque (Nm)',
        title='Real-time Speed and Torque Data'
    )

    # 更新x轴范围
    fig.update_xaxes(range=[max(0, n - 10), n + 1])

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
