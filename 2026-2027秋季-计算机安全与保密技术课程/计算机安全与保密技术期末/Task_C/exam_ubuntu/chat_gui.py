import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, filedialog
import socket
import threading
from cryptography.fernet import Fernet


class SecureChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SecureChat - 加密通信")
        self.root.geometry("450x650")
        self.root.configure(bg="#f0f2f5")

        self.sock = None
        self.fernet = None
        self.is_server = False

        # 1. 第一步：弹出文件选择框，让用户选密钥
        self.root.withdraw()  # 先隐藏主窗口
        key_path = filedialog.askopenfilename(
            title="请选择加密密钥文件 (选 badkey.bin 可演示解密失败)",
            initialfile="key.bin",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )

        if not key_path:
            messagebox.showwarning("取消", "未选择密钥文件，程序退出。")
            self.root.destroy()
            return

        # 加载选择的密钥
        try:
            key = open(key_path, "rb").read().strip()
            self.fernet = Fernet(key)
            print(f"已加载密钥: {key_path}")
        except Exception as e:
            messagebox.showerror("错误", f"读取密钥失败: {e}")
            self.root.destroy()
            return

        self.main_frame = tk.Frame(self.root, bg="#f0f2f5")

        # 2. 第二步：选择作为服务端还是客户端
        self.ask_mode()

    def ask_mode(self):
        answer = messagebox.askyesno("模式选择",
                                     "你要作为【服务端】启动吗？\n\n选 是(Yes)：等待别人连接\n选 否(No)：主动连接别人")

        if answer:
            self.is_server = True
            self.start_server()
        else:
            self.is_server = False
            self.start_client()

    def start_server(self):
        port = simpledialog.askinteger("服务端设置", "请输入监听端口 (默认5000):", initialvalue=5000)
        if not port: self.root.destroy(); return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', port))
        self.sock.listen(1)

        self.setup_ui(f"[服务端] 监听端口 {port}")

        def wait_conn():
            try:
                self.conn, addr = self.sock.accept()
                self.root.after(0, lambda: self.on_connected(f"已连接客户端: {addr[0]}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"监听失败: {e}"))

        threading.Thread(target=wait_conn, daemon=True).start()

    def start_client(self):
        host = simpledialog.askstring("客户端设置", "请输入服务端 IP (默认 127.0.0.1):", initialvalue="127.0.0.1")
        if not host: self.root.destroy(); return
        port = simpledialog.askinteger("客户端设置", "请输入服务端端口 (默认5000):", initialvalue=5000)
        if not port: self.root.destroy(); return

        self.setup_ui(f"[客户端] 尝试连接 {host}:{port}")

        def connect():
            try:
                self.conn = socket.create_connection((host, port))
                self.root.after(0, lambda: self.on_connected("连接服务端成功！"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("连接失败", str(e)))
                self.root.destroy()

        threading.Thread(target=connect, daemon=True).start()

    def setup_ui(self, status_text):
        self.root.deiconify()
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.status_bar = tk.Label(self.main_frame, text=status_text, bg="#2ecc71", fg="white",
                                   font=("Arial", 10, "bold"), pady=8)
        self.status_bar.pack(fill=tk.X)

        self.chat_area = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, state='disabled', bg="#e5ddd5",
                                                   font=("Arial", 11), bd=0)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.chat_area.tag_configure("other", justify='left', background="#ffffff", lmargin1=10, lmargin2=10,
                                     rmargin=50, spacing1=5, spacing3=5)
        self.chat_area.tag_configure("me", justify='right', background="#dcf8c6", lmargin1=50, lmargin2=50, rmargin=10,
                                     spacing1=5, spacing3=5)

        bottom_frame = tk.Frame(self.main_frame, bg="#f0f2f5")
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.msg_entry = tk.Entry(bottom_frame, font=("Arial", 12), bg="white", relief="flat")
        self.msg_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=8)
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        self.send_btn = tk.Button(bottom_frame, text="发送", bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                                  relief="flat", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT, padx=(10, 0), ipadx=10, ipady=5)

    def on_connected(self, msg):
        self.status_bar.config(text="🟢 已连接 - " + msg, bg="#27ae60")
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def receive_messages(self):
        fin = self.conn.makefile('rb')
        while True:
            try:
                line = fin.readline()
                if not line: break
                line = line.strip()
                if not line: continue

                try:
                    decrypted_msg = self.fernet.decrypt(line).decode('utf-8')
                    self.root.after(0, self.display_message, decrypted_msg, "other")
                except Exception as e:
                    self.root.after(0, self.display_message, "⚠️ [解密失败！密钥不匹配]", "other")
            except Exception:
                break
        self.root.after(0, lambda: self.status_bar.config(text="🔴 连接已断开", bg="#e74c3c"))

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg: return
        self.msg_entry.delete(0, tk.END)

        try:
            encrypted_msg = self.fernet.encrypt(msg.encode('utf-8'))
            self.conn.sendall(encrypted_msg + b'\n')
            self.display_message(msg, "me")
        except Exception as e:
            messagebox.showerror("发送失败", "连接已断开")

    def display_message(self, msg, sender):
        self.chat_area.config(state='normal')
        if sender == "me":
            self.chat_area.insert(tk.END, f"\n{msg}\n ", "me")
        else:
            self.chat_area.insert(tk.END, f"\n {msg}\n", "other")
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)


if __name__ == '__main__':
    root = tk.Tk()
    app = SecureChatGUI(root)
    root.mainloop()