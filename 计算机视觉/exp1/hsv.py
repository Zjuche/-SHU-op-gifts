import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os


def display_hsv_channels_with_chinese(input_path, font_path=None):
    """
    显示RGB图像及其HSV各通道分量，支持中文标题
    """
    # 读取图像
    img_bgr = cv2.imread(input_path)
    if img_bgr is None:
        print(f"错误：无法读取图片 '{input_path}'")
        return

    # 转换为RGB顺序（供Pillow使用）
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # 转换为HSV颜色空间
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # 分离HSV通道
    h, s, v = cv2.split(img_hsv)

    # 创建纯色相可视化图像
    hsv_combined = np.zeros_like(img_bgr)
    hsv_combined[:, :, 0] = h
    hsv_combined[:, :, 1] = 255
    hsv_combined[:, :, 2] = 255
    hue_visualization = cv2.cvtColor(hsv_combined, cv2.COLOR_HSV2BGR)

    # 处理中文字体
    def load_font(size=20):
        """尝试加载中文字体"""
        try:
            # 如果提供了字体路径
            if font_path and os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)

            # 尝试常见中文字体路径
            font_paths = [
                "simhei.ttf",  # 黑体
                "msyh.ttc",  # 微软雅黑
                "simsun.ttc",  # 宋体
                r"C:\Windows\Fonts\simhei.ttf",
                r"C:\Windows\Fonts\msyh.ttc",
                r"/System/Library/Fonts/PingFang.ttc",  # macOS
                r"/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"  # Linux
            ]

            for fp in font_paths:
                if os.path.exists(fp):
                    return ImageFont.truetype(fp, size)

            # 尝试默认字体（可能不支持中文）
            return ImageFont.load_default()
        except:
            return ImageFont.load_default()

    # 创建带中文标题的显示面板
    def create_chinese_panel():
        """创建包含所有通道和中文标题的面板"""
        # 调整各通道图像大小
        size = (300, 300)

        # 缩放所有图像
        orig = cv2.resize(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR), size)
        h_img = cv2.resize(cv2.cvtColor(h, cv2.COLOR_GRAY2BGR), size)
        s_img = cv2.resize(cv2.cvtColor(s, cv2.COLOR_GRAY2BGR), size)
        v_img = cv2.resize(cv2.cvtColor(v, cv2.COLOR_GRAY2BGR), size)
        hsv_img = cv2.resize(cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR), size)
        hue_viz = cv2.resize(hue_visualization, size)

        # 创建空白面板（白色背景）
        panel = np.ones((800, 1000, 3), dtype=np.uint8) * 255

        # 放置图像
        panel[60:360, 20:320] = orig
        panel[60:360, 350:650] = h_img
        panel[60:360, 680:980] = s_img
        panel[400:700, 20:320] = v_img
        panel[400:700, 350:650] = hsv_img
        panel[400:700, 680:980] = hue_viz

        # 转换为PIL图像添加中文文本
        pil_img = Image.fromarray(panel)
        draw = ImageDraw.Draw(pil_img)

        # 加载中文字体
        font = load_font(24)

        # 添加中文标题
        titles = [
            ("原始RGB图像", (80, 20)),
            ("H通道 (色相)", (410, 20)),
            ("S通道 (饱和度)", (740, 20)),
            ("V通道 (明度)", (80, 360)),
            ("HSV合成图像", (410, 360)),
            ("纯色相可视化", (740, 360))
        ]

        for text, (x, y) in titles:
            draw.text((x, y), text, font=font, fill=(0, 0, 0))

        # 添加操作提示
        font_small = load_font(20)
        draw.text((50, 730), "按 ESC 键退出程序", font=font_small, fill=(255, 0, 0))

        # 转回OpenCV格式
        return np.array(pil_img)

    # 创建窗口并显示
    window_name = "HSV 颜色空间分析"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # 实时更新显示
    while True:
        display_panel = create_chinese_panel()
        cv2.imshow(window_name, display_panel)

        # 检测按键
        key = cv2.waitKey(30)
        if key == 27:  # ESC键退出
            break

    cv2.destroyAllWindows()
    print("显示结束，程序退出")


# 使用示例
if __name__ == "__main__":
    # 替换为你的图片路径
    input_image = "hmny.jpg"

    # 尝试指定字体路径（可选）
    # font_path = r"C:\Windows\Fonts\simhei.ttf"  # Windows系统字体
    font_path = None  # 自动检测

    display_hsv_channels_with_chinese(input_image, font_path)