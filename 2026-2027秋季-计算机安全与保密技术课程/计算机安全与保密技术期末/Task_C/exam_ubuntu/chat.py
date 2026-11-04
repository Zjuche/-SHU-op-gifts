import socket
import threading
import argparse
from cryptography.fernet import Fernet


def recv_loop(sock, f):
    """接收消息的子线程"""
    fin = sock.makefile('rb')
    while True:
        line = fin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            # 尝试解密
            msg = f.decrypt(line).decode('utf-8')
            print(f'\n[收到密文并解密] {msg}\n> ', end='', flush=True)
        except Exception as e:
            # 密钥不对会报错
            print(f'\n[解密失败！密钥不匹配]\n> ', end='', flush=True)


def main():
    # 解析命令行参数
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['server', 'client'], required=True, help='作为服务端还是客户端')
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=5000)
    p.add_argument('--key', default='key.bin', help='密钥文件路径')
    args = p.parse_args()

    # 读取密钥
    try:
        key = open(args.key, 'rb').read().strip()
        f = Fernet(key)
    except Exception as e:
        print(f"读取密钥失败，请检查密钥文件是否存在: {e}")
        return

    # 根据模式建立连接
    if args.mode == 'server':
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.host, args.port))
        s.listen(1)
        print(f'[服务端] 正在监听 {args.host}:{args.port}，等待连接...')
        conn, addr = s.accept()
        print(f'[服务端] 客户端已连接: {addr}')
    else:
        conn = socket.create_connection((args.host, args.port))
        print(f'[客户端] 成功连接到 {args.host}:{args.port}')

    # 启动子线程接收消息
    threading.Thread(target=recv_loop, args=(conn, f), daemon=True).start()

    print("======================================")
    print("你可以开始聊天了，输入 /quit 退出。")
    print("======================================")

    # 主线程循环发送消息
    while True:
        msg = input('> ')
        if msg.strip() == '/quit':
            break

        # 加密消息并发送
        encrypted_msg = f.encrypt(msg.encode('utf-8'))
        conn.sendall(encrypted_msg + b'\n')

        # 新增：打印提示，让你确认消息已经发出去了
        # 只截取前20个字符展示，让你直观看到这是一堆乱码（密文）
        print(f'[发送密文] {encrypted_msg.decode()[:20]}... (已发送)')

    conn.close()


if __name__ == '__main__':
    main()