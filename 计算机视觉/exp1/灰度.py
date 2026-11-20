from PIL import Image


def convert_to_grayscale(input_path, output_path):
    """
    将彩色图片转换为灰度图并保存

    参数:
    input_path -- 输入图片路径
    output_path -- 输出图片路径
    """
    try:
        # 打开彩色图片
        with Image.open(input_path) as img:
            # 转换为灰度图 ('L' 表示8位灰度)
            grayscale_img = img.convert('L')

            # 保存灰度图
            grayscale_img.save(output_path)
            print(f"转换成功！灰度图已保存至: {output_path}")

            # 可选：显示图片
            # grayscale_img.show()

    except FileNotFoundError:
        print(f"错误：找不到输入文件 '{input_path}'")
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")


# 使用示例
if __name__ == "__main__":
    input_image = "guide.png"  # 替换为你的输入图片路径
    output_image = "gray.png"  # 替换为你的输出图片路径

    convert_to_grayscale(input_image, output_image)