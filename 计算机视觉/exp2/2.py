import cv2
import numpy as np

# 1. 读取图片并转为灰度
image = cv2.imread("qxj.jpeg")
if image is None:
    raise FileNotFoundError("输入图片未找到")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 2. 计算中心点及最大内接圆半径
h, w = gray.shape
cx, cy = w // 2, h // 2
max_radius = min(h, w) // 2  # 确保圆形不超出图像边界

# 3. 裁剪圆形外接正方形 (尺寸: 2r x 2r)
start_x, start_y = cx - max_radius, cy - max_radius
cropped_square = gray[start_y:start_y+2*max_radius,
                      start_x:start_x+2*max_radius]

# 4. 缩放至目标尺寸 (边长≥500)
target_size = max(2 * max_radius, 500)  # 保持不小于500px
square_resized = cv2.resize(cropped_square, (target_size, target_size),
                            interpolation=cv2.INTER_CUBIC)

# 5. 创建圆形掩膜 (保留5px边界)
mask = np.zeros((target_size, target_size), dtype=np.uint8)
cv2.circle(mask, (target_size//2, target_size//2),
           target_size//2 - 5, 255, -1)
result = cv2.bitwise_and(square_resized, square_resized, mask=mask)

# 6. 保存结果
cv2.imwrite("output.jpg", result)