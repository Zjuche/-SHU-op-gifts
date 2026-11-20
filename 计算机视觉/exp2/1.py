import cv2
import numpy as np
import time

# 读取图片（请替换为您的图片路径）
image_path = 'qxj.jpeg'  # 修改为您的图片路径
image = cv2.imread(image_path)
if image is None:
    print(f"错误: 无法读取图片 '{image_path}'，请检查路径是否正确")
    exit()

# 获取原始图片尺寸
original_height, original_width = image.shape[:2]

# 1. 平移
def translate(img, x, y):
    rows, cols = img.shape[:2]
    M = np.float32([[1, 0, x], [0, 1, y]])
    translated = cv2.warpAffine(img, M, (cols, rows), borderValue=(0, 0, 0))
    return translated

# 2. 缩放
def resize(img, width=None, height=None, scale=None):
    if scale:
        return cv2.resize(img, None, fx=scale, fy=scale)
    else:
        return cv2.resize(img, (width, height))

# 3. 翻转
def flip(img, mode):
    if mode == 'horizontal':
        return cv2.flip(img, 1)
    elif mode == 'vertical':
        return cv2.flip(img, 0)
    else:  # horizontal+vertical
        return cv2.flip(img, -1)

# 4. 旋转
def rotate(img, angle, center=None):
    (h, w) = img.shape[:2]
    if center is None:
        center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), borderValue=(0, 0, 0))
    return rotated

# 5. 缩略图
def thumbnail(img, scale=0.3):
    small = cv2.resize(img, None, fx=scale, fy=scale)
    s_h, s_w = small.shape[:2]
    result = img.copy()
    result[0:s_h, 0:s_w] = small
    return result

# 显示函数：避免窗口重叠
def show_image(title, img, delay=1500):
    cv2.imshow(title, img)
    cv2.waitKey(delay)

# 显示原始图片
show_image('原始图片', image)

# (1) 平移
translated = translate(image, 100, 150)
show_image('平移 (x+100, y+150)', translated)

# (2) 缩放
scaled_to_size = resize(image, width=1024, height=768)
show_image('缩放至1024x768', scaled_to_size)

scaled_by_scale = resize(image, scale=0.6)
show_image('按比例缩小60%', scaled_by_scale)

# (3) 翻转
flip_h = flip(image, 'horizontal')
show_image('水平翻转', flip_h)

flip_v = flip(image, 'vertical')
show_image('垂直翻转', flip_v)

flip_both = flip(image, 'both')
show_image('水平+垂直翻转', flip_both)

# (4) 旋转 (以图片中心旋转45度)
rotated = rotate(image, 45)
show_image('旋转45度', rotated)

# (5) 缩略图
thumb = thumbnail(image, 0.4)
show_image('左上角缩略图', thumb)

# 最后关闭所有窗口
cv2.destroyAllWindows()
print("所有图片处理已完成并显示")