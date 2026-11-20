import cv2

# 创建视频捕获对象
cap = cv2.VideoCapture('Waymo.mp4')  # 确保视频文件在当前目录

# 检查视频是否成功打开
if not cap.isOpened():
    print("Error: 无法打开视频文件")
    exit()

print(f"视频信息: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} 分辨率, "
      f"帧率: {cap.get(cv2.CAP_PROP_FPS):.2f}")

# 循环读取并播放视频
while cap.isOpened():
    ret, frame = cap.read()

    # 检测是否读到有效帧
    if not ret:
        print("视频播放完毕")
        break

    # 显示当前帧
    cv2.imshow('Waymo Video', frame)

    # 控制播放速度 (25帧/秒)
    key = cv2.waitKey(40)  # 40ms延迟 ≈ 25fps

    # 按ESC或'q'退出播放
    if key == 27 or key == ord('q'):
        break 

# 释放资源
cap.release()
cv2.destroyAllWindows()