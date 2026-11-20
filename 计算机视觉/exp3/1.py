import cv2
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys

# 修复1: 设置Agg后端避免Tkinter问题
plt.switch_backend('Agg')  # 使用非交互式后端

# 1. 读取图片
try:
    image = cv2.imread('ysl.jpg')
    if image is None:
        raise FileNotFoundError("无法加载图片，请检查路径和文件名")
except Exception as e:
    print(f"图片读取错误: {e}", file=sys.stderr)
    sys.exit(1)

# 修复2: 缩小图像尺寸减少内存需求
image = cv2.resize(image, (300, 200))  # 调整为300×200像素

rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
hsv_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)

# 2. 分离通道
r, g, b = cv2.split(rgb_image)
h, s, v = cv2.split(hsv_image)

# 3. 创建三维网格 (使用缩小后的尺寸)
height, width = r.shape[:2]
x = np.arange(0, width, 1)
y = np.arange(0, height, 1)
X, Y = np.meshgrid(x, y)

# 4. 创建图表
fig = plt.figure(figsize=(18, 12))

# 修复3: 简化可视化并减少点数量
def plot_3d_channel(ax, data, title, cmap):
    """简化版3D绘图函数"""
    # 每隔5个点采样减少数据量
    ax.plot_surface(X[::5, ::5], Y[::5, ::5], data[::5, ::5],
                   cmap=cmap, rstride=3, cstride=3, alpha=0.7)
    ax.set_title(title, fontsize=12)
    ax.set_zlim(0, 255)
    ax.view_init(elev=30, azim=45)  # 调整视角

# R通道
ax1 = fig.add_subplot(231, projection='3d')
plot_3d_channel(ax1, r, 'Red Channel 3D', 'Reds')

# G通道
ax2 = fig.add_subplot(232, projection='3d')
plot_3d_channel(ax2, g, 'Green Channel 3D', 'Greens')

# B通道
ax3 = fig.add_subplot(233, projection='3d')
plot_3d_channel(ax3, b, 'Blue Channel 3D', 'Blues')

# 2D通道可视化
def plot_2d_channel(ax, channel, title, cmap):
    ax.imshow(channel, cmap=cmap)
    ax.set_title(title, fontsize=10)
    ax.axis('off')

plot_2d_channel(fig.add_subplot(234), r, 'Red Channel', 'Reds')
plot_2d_channel(fig.add_subplot(235), g, 'Green Channel', 'Greens')
plot_2d_channel(fig.add_subplot(236), b, 'Blue Channel', 'Blues')

# 修复4: 保存图像而不是显示
plt.tight_layout()
plt.savefig('output_visualization.png', dpi=100)  # 保存为文件
print("可视化结果已保存至 output_visualization.png")

# 保存HSV通道
cv2.imwrite('h_channel.jpg', h)
cv2.imwrite('s_channel.jpg', s)
cv2.imwrite('v_channel.jpg', v)
print("HSV通道已保存")