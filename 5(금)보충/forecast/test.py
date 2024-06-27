import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

# 초기 데이터 설정
x_data = []
y_data = []

# 피겨와 축 생성
fig, ax = plt.subplots()
ln, = plt.plot([], [], 'ro')

# 그래프 초기화 함수
def init():
    ax.set_xlim(0, 2 * np.pi)
    ax.set_ylim(-1, 1)
    return ln,

# 그래프 업데이트 함수
def update(frame):
    x_data.append(frame)
    y_data.append(np.sin(frame))
    ln.set_data(x_data, y_data)
    return ln,

# 애니메이션 생성
ani = FuncAnimation(fig, update, frames=np.linspace(0, 2 * np.pi, 128),
                    init_func=init, blit=True)

# 그래프 보여주기
plt.show()
