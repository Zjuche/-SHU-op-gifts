import cv2
import os
import sys
import numpy as np
import urllib.request
import tempfile

print("=" * 60)
print("人脸检测程序启动")
print("=" * 60)

# 创建临时目录用于存放下载的XML文件
TEMP_DIR = tempfile.mkdtemp(prefix="opencv_data_")
print(f"临时目录: {TEMP_DIR}")

# 设置项目目录
PROJECT_DIR = r"D:\学习\学校\专业课\计算机视觉\exp5"
print(f"项目目录: {PROJECT_DIR}")

# 尝试切换到项目目录
try:
    os.chdir(PROJECT_DIR)
    print(f"当前工作目录: {os.getcwd()}")
    print(f"目录内容: {os.listdir('.')}")
except Exception as e:
    print(f"切换目录失败: {str(e)}")
    print(f"当前工作目录: {os.getcwd()}")

# Haar级联文件URL (GitHub直链)
XML_URL = "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/haarcascade_frontalface_default.xml"
XML_PATH = os.path.join(TEMP_DIR, "haarcascade_frontalface_default.xml")
print(f"XML文件路径: {XML_PATH}")


def download_file(url, save_path):
    """下载文件并保存"""
    try:
        print(f"正在下载文件: {url}")
        urllib.request.urlretrieve(url, save_path)
        print(f"✅ 文件下载成功: {save_path}")

        # 验证文件大小
        file_size = os.path.getsize(save_path)
        print(f"文件大小: {file_size / 1024:.1f} KB")
        if file_size < 900 * 1024:  # 小于900KB可能不完整
            raise ValueError("文件大小异常，可能下载不完整")

        return True
    except Exception as e:
        print(f"❌ 下载失败: {str(e)}")
        return False


def load_classifier():
    """加载分类器 - 使用多种方法确保成功"""
    # 方法1：使用下载的文件
    if os.path.exists(XML_PATH):
        cascade = cv2.CascadeClassifier(XML_PATH)
        if not cascade.empty():
            print("✅ 使用下载的分类器文件")
            return cascade

    # 方法2：使用其他备选分类器
    alt_classifiers = [
        'haarcascade_frontalface_alt.xml',
        'haarcascade_frontalface_alt2.xml',
        'haarcascade_frontalface_alt_tree.xml'
    ]

    # 尝试在多个可能的位置查找
    search_paths = [
        os.path.join(os.path.dirname(cv2.__file__), 'data') if hasattr(cv2, '__file__') else '',
        os.path.join(sys.prefix, 'Lib', 'site-packages', 'cv2', 'data'),
        TEMP_DIR
    ]

    print("\n搜索备选分类器...")
    for path in search_paths:
        if not os.path.exists(path):
            continue

        print(f"搜索路径: {path}")
        files = os.listdir(path)
        print(f"文件列表: {files}")

        for classifier in alt_classifiers:
            test_path = os.path.join(path, classifier)
            if os.path.exists(test_path):
                print(f"尝试加载: {test_path}")
                cascade = cv2.CascadeClassifier(test_path)
                if not cascade.empty():
                    print(f"✅ 使用备选分类器: {classifier}")
                    return cascade

    return None


# 下载分类器文件（如果不存在）
if not os.path.exists(XML_PATH):
    download_file(XML_URL, XML_PATH)
else:
    print(f"XML文件已存在: {XML_PATH}")

# 尝试加载分类器
face_cascade = load_classifier()

# 如果仍然失败，尝试重新安装OpenCV
if face_cascade is None or face_cascade.empty():
    print("\n❌ 无法加载分类器，尝试重新安装OpenCV...")
    try:
        import subprocess
        import sys

        # 获取当前Python解释器路径
        python_exe = sys.executable
        if not python_exe:
            raise ValueError("无法获取Python解释器路径")

        # 获取pip路径
        pip_path = os.path.join(os.path.dirname(python_exe), 'pip.exe')
        if not os.path.exists(pip_path):
            pip_path = os.path.join(os.path.dirname(python_exe), 'Scripts', 'pip.exe')

        print(f"Python路径: {python_exe}")
        print(f"pip路径: {pip_path}")

        # 卸载现有OpenCV
        print("卸载OpenCV...")
        subprocess.run([pip_path, 'uninstall', '-y', 'opencv-python', 'opencv-python-headless'], check=True)

        # 安装指定版本OpenCV
        print("安装OpenCV 4.5.5...")
        subprocess.run([pip_path, 'install', 'opencv-python-headless==4.5.5.64'], check=True)

        # 重试加载分类器
        import cv2

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        if face_cascade.empty():
            raise RuntimeError("重新安装后仍然无法加载分类器")

        print("✅ OpenCV重新安装成功，分类器加载完成")
    except Exception as e:
        print(f"❌ 重新安装失败: {str(e)}")
        print("\n请手动执行以下命令:")
        print(f"  {pip_path} uninstall -y opencv-python opencv-python-headless")
        print(f"  {pip_path} install opencv-python-headless==4.5.5.64")
        exit(1)


# 人脸检测函数
def detect_and_save(image_path):
    """检测人脸并保存结果"""
    try:
        print(f"\n处理图像: {image_path}")

        # 检查图片是否存在
        if not os.path.exists(image_path):
            print(f"❌ 图片不存在: {image_path}")
            return None, 0

        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ 无法读取图片: {image_path}")
            return None, 0

        # 处理PNG透明通道
        if len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # 转为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 人脸检测（自适应参数）
        scale_factor = 1.05
        min_neighbors = 5
        min_size = (30, 30)

        print(f"检测参数: scaleFactor={scale_factor}, minNeighbors={min_neighbors}, minSize={min_size}")

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size
        )

        print(f"检测到 {len(faces)} 个人脸")

        # 绘制矩形框
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 保存结果
        filename, ext = os.path.splitext(image_path)
        output_path = f"{filename}_result{ext}"
        cv2.imwrite(output_path, img)
        print(f"✅ 结果保存至: {output_path}")

        # 显示结果（2秒）
        cv2.imshow('检测结果', img)
        cv2.waitKey(2000)
        cv2.destroyAllWindows()

        return output_path, len(faces)
    except Exception as e:
        print(f"❌ 处理图像时出错: {str(e)}")
        return None, 0


# 要处理的图像列表
image_files = [
    'bobo.jpeg',
    'ljfd.jpeg',
    'ln.jpeg',
    'ysl.jpg',
    'bg.jpeg'
]

# 检查图像是否存在
valid_images = []
for img in image_files:
    if os.path.exists(img):
        valid_images.append(img)
        print(f"✅ 找到图像: {img}")
    else:
        print(f"❌ 图像不存在: {img}")

if not valid_images:
    print("\n❌ 错误: 没有找到任何图像文件")
    print("当前目录内容:")
    for f in os.listdir('.'):
        print(f" - {f}")
    exit(1)

# 处理所有图像
total_faces = 0
print("\n" + "=" * 50)
print(f"开始处理 {len(valid_images)} 张图像")
print("=" * 50)

results = []
for img_path in valid_images:
    result, faces = detect_and_save(img_path)
    if result:
        results.append((result, faces))
        total_faces += faces

# 打印最终报告
print("\n" + "=" * 60)
print("人脸检测报告")
print("=" * 60)
print(f"处理图像数量: {len(valid_images)}")
print(f"检测到人脸总数: {total_faces}")
print("\n结果文件:")
for result, faces in results:
    print(f" - {result} (检测到 {faces} 张人脸)")

print("\n" + "=" * 60)
print("程序执行完成")
print("=" * 60)

# 提示用户打开结果目录
print(f"\n请手动打开结果目录:")
print(PROJECT_DIR)