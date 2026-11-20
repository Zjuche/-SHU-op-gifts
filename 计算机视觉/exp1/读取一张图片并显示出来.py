from PIL import Image

# 读取图片（支持JPG/PNG/BMP等格式）
image = Image.open('guide.png')  # 替换为你的图片路径

# 显示图片
image.show()

# 可选：获取图片信息
print(f"格式: {image.format}, 尺寸: {image.size}, 模式: {image.mode}")