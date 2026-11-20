import cv2
import numpy as np
import matplotlib
import sys
import os

# 强制使用非Tk后端
matplotlib.use('Agg')  # 使用纯图像后端
import matplotlib.pyplot as plt

# 1. 读取彩色图像 (改为PNG格式)
image_path = 'home_color.png'
if not os.path.exists(image_path):
    # 尝试JPEG格式作为备选
    image_path = 'home_color.jpg'
    if not os.path.exists(image_path):
        print(f"错误: 无法找到 {image_path}", file=sys.stderr)
        sys.exit(1)

img_color = cv2.imread(image_path)
if img_color is None:
    print(f"错误: 无法加载 {image_path}", file=sys.stderr)
    sys.exit(1)

# 转换为RGB格式
img_rgb = cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB)

# 2. 灰度化并绘制直方图
img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

# 创建结果图像 - 调整为更合适的尺寸
result_image = np.zeros((900, 1200, 3), dtype=np.uint8) + 255  # 白色背景


# 修复fig_to_cv2函数
def fig_to_cv2(fig):
    fig.canvas.draw()
    # 获取RGBA缓冲区的宽度和高度
    w, h = fig.canvas.get_width_height()

    # 使用buffer_rgba获取图像数据
    buf = fig.canvas.buffer_rgba()
    data = np.frombuffer(buf, dtype=np.uint8)
    data = data.reshape((h, w, 4))  # RGBA格式

    # 转换为BGR格式并去除alpha通道
    return cv2.cvtColor(data, cv2.COLOR_RGBA2BGR)


# 2.1 灰度图及其直方图
fig1 = plt.figure(figsize=(12, 5))
ax1 = fig1.add_subplot(121)
ax1.imshow(img_gray, cmap='gray')
ax1.set_title('Grayscale Image')
ax1.axis('off')

ax2 = fig1.add_subplot(122)
ax2.hist(img_gray.ravel(), bins=256, range=[0, 256], color='gray')
ax2.set_title('Grayscale Histogram')
ax2.set_xlabel('Pixel Value')
ax2.set_ylabel('Frequency')
plt.tight_layout()
gray_result = fig_to_cv2(fig1)
plt.close(fig1)

# 调整大小以适应布局
gray_result_resized = cv2.resize(gray_result, (550, 350))
result_image[50:400, 50:600] = gray_result_resized

# 3. 彩色直方图
fig2 = plt.figure(figsize=(12, 5))
ax3 = fig2.add_subplot(121)
ax3.imshow(img_rgb)
ax3.set_title('Color Image')
ax3.axis('off')

ax4 = fig2.add_subplot(122)
colors = ('b', 'g', 'r')
for i, col in enumerate(colors):
    hist = cv2.calcHist([img_rgb], [i], None, [256], [0, 256])
    ax4.plot(hist, color=col)
ax4.set_title('Color Histogram')
ax4.set_xlabel('Pixel Value')
ax4.set_ylabel('Frequency')
plt.tight_layout()
color_result = fig_to_cv2(fig2)
plt.close(fig2)

# 调整大小以适应布局
color_result_resized = cv2.resize(color_result, (550, 350))
result_image[50:400, 600:1150] = color_result_resized

# 4. ROI处理
# 获取图像尺寸
h, w = img_rgb.shape[:2]

# 定义ROI区域，确保在图像范围内
roi_x1, roi_x2 = max(0, min(50, w - 10)), min(w, max(100, 60))  # x:50-100
roi_y1, roi_y2 = max(0, min(100, h - 10)), min(h, max(200, 110))  # y:100-200

roi = img_rgb[roi_y1:roi_y2, roi_x1:roi_x2]

# 创建ROI的mask
mask = np.zeros(img_gray.shape[:2], dtype=np.uint8)
mask[roi_y1:roi_y2, roi_x1:roi_x2] = 255

# 提取ROI区域
roi_masked = cv2.bitwise_and(img_rgb, img_rgb, mask=mask)

# 4.1 原始图像（标记ROI区域）
img_rgb_with_roi = img_rgb.copy()
cv2.rectangle(img_rgb_with_roi, (roi_x1, roi_y1), (roi_x2, roi_y2), (255, 0, 0), 2)

# 创建ROI分析图像
roi_display = np.zeros((350, 850, 3), dtype=np.uint8) + 255

# 添加所有ROI分析结果
roi_display[10:160, 10:260] = cv2.resize(img_rgb_with_roi, (250, 150))
cv2.putText(roi_display, 'Original w/ROI', (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

roi_display[10:160, 290:540] = cv2.resize(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), (250, 150))
cv2.putText(roi_display, 'ROI Mask', (300, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

roi_display[10:160, 570:820] = cv2.resize(roi_masked, (250, 150))
cv2.putText(roi_display, 'Extracted ROI', (580, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

# ROI直方图
fig3 = plt.figure(figsize=(8, 3))
for i, col in enumerate(colors):
    hist = cv2.calcHist([roi], [i], None, [256], [0, 256])
    plt.plot(hist, color=col)
plt.title('ROI Color Histogram')
plt.xlabel('Pixel Value')
plt.ylabel('Frequency')
plt.tight_layout()
roi_hist = fig_to_cv2(fig3)
plt.close(fig3)

roi_display[170:330, 100:750] = cv2.resize(roi_hist, (650, 160))

# 添加到最终结果
result_image[420:770, 175:1025] = roi_display

# 添加标题
cv2.putText(result_image, 'Histogram Comparison', (400, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
cv2.putText(result_image, 'ROI Analysis', (500, 400),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

# 保存并显示结果
output_file = 'result_visualization.jpg'
cv2.imwrite(output_file, result_image)
print(f"结果已保存至 {output_file}")

# 使用OpenCV显示结果
cv2.namedWindow('Computer Vision Experiment Results', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Computer Vision Experiment Results', 1000, 700)  # 更合理的窗口尺寸
cv2.imshow('Computer Vision Experiment Results', result_image)
cv2.waitKey(0)
cv2.destroyAllWindows()