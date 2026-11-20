    from PIL import Image, ImageDraw, ImageFont

    # 1. 加载图片
    image = Image.open("guide.png")  # 替换为你的图片路径

    # 2. 创建绘图对象
    draw = ImageDraw.Draw(image)

    # 3. 设置文字内容和样式
    text = "23122673 张哲睿"  # 要插入的文字
    text_color = (255, 0, 0)  # RGB颜色 (红色)
    text_position = (50, 50)  # 文字左上角坐标 (x, y)

    # 4. 设置字体（重要！）
    try:
        # Windows系统常用字体路径
        font = ImageFont.truetype("simhei.ttf", 40)  # 黑体
    except:
        try:
            # macOS系统常用字体路径
            font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 40)
        except:
            # 备用方案：使用默认字体（可能不支持中文）
            font = ImageFont.load_default()
            print("警告：使用默认字体，中文字符可能显示异常")

    # 5. 添加文字到图片
    draw.text(text_position, text, fill=text_color, font=font)

    # 6. 保存处理后的图片
    output_path = "output.png"  # 输出文件路径
    image.save(output_path)
    print(f"图片已保存至：{output_path}")

    # 可选：显示图片（需要桌面环境）
    # image.show()