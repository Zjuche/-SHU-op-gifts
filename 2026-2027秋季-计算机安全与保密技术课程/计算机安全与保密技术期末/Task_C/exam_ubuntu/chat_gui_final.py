import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext, filedialog
import socket
import threading
import os
from cryptography.fernet import Fernet, InvalidToken


class SecureChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SecureChat Pro - 加密通信与文件传输")
        self.root.geometry("480x680")
        self.root.configure(bg="#f0f2f5")

        self.sock = None
        self.fernet = None
        self.auth_fail_count = 0  # 用于防御暴力破解

        self.root.withdraw()
        key_path = filedialog.askopenfilename(title="请选择加密密钥文件", initialfile="key.bin",
                                              filetypes=[("Binary files", "*.bin")])
        if not key_path: self.root.destroy(); return

        try:
            key = open(key_path, "rb").read().strip()
            self.fernet = Fernet(key)
        except Exception as e:
            messagebox.showerror("错误", f"读取密钥失败: {e}")
            self.root.destroy();
            return

        self.main_frame = tk.Frame(self.root, bg="#f0f2f5")
        self.ask_mode()

    def ask_mode(self):
        answer = messagebox.askyesno("模式", "作为服务端启动？(Yes=服务端, No=客户端)")
        if answer:
            self.start_server()
        else:
            self.start_client()

    def start_server(self):
        port = simpledialog.askinteger("端口", "监听端口:", initialvalue=5000)
        if not port: self.root.destroy(); return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', port))
        self.sock.listen(1)
        self.setup_ui(f"[服务端] 监听 {port}...")

        def wait_conn():
            try:
                conn, addr = self.sock.accept()
                self.conn = conn
                self.root.after(0, lambda: self.on_connected(f"已连接: {addr[0]}"))
            except Exception:
                pass

        threading.Thread(target=wait_conn, daemon=True).start()

    def start_client(self):
        host = simpledialog.askstring("客户端", "IP地址:", initialvalue="127.0.0.1")
        if not host: self.root.destroy(); return
        port = simpledialog.askinteger("客户端", "端口:", initialvalue=5000)
        if not port: self.root.destroy(); return

        self.setup_ui(f"[客户端] 连接 {host}:{port}...")

        def connect():
            try:
                self.conn = socket.create_connection((host, port))
                self.root.after(0, lambda: self.on_connected("连接成功！"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("失败", str(e)))
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
        self.chat_area.tag_configure("error", justify='center', background="#ffcccc", foreground="red",
                                     font=("Arial", 10, "bold"))

        bottom_frame = tk.Frame(self.main_frame, bg="#f0f2f5")
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # 新增：发送文件按钮
        self.file_btn = tk.Button(bottom_frame, text="📁", bg="#f39c12", fg="white", font=("Arial", 12), relief="flat",
                                  command=self.send_file)
        self.file_btn.pack(side=tk.LEFT, padx=(0, 5), ipady=3)

        self.msg_entry = tk.Entry(bottom_frame, font=("Arial", 12), bg="white", relief="flat")
        self.msg_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=8)
        self.msg_entry.bind("<Return>", lambda event: self.send_message())

        self.send_btn = tk.Button(bottom_frame, text="发送", bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                                  relief="flat", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT, padx=(5, 0), ipadx=10, ipady=5)

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

                # 解析数据类型（TEXT 或 FILE）
                if line.startswith(b"TEXT:"):
                    try:
                        decrypted_msg = self.fernet.decrypt(line[5:]).decode('utf-8')
                        self.root.after(0, self.display_message, decrypted_msg, "other")
                    except InvalidToken:
                        self.auth_fail_count += 1
                        self.root.after(0, self.display_error,
                                        f"⚠️ 解密失败！密钥不匹配 (尝试次数: {self.auth_fail_count}/3)")
                        if self.auth_fail_count >= 3:
                            self.root.after(0, self.lock_down)
                elif line.startswith(b"FILE:"):
                    # 文件格式：FILE:文件加密名:文件加密内容
                    parts = line[5:].split(b":", 1)
                    if len(parts) == 2:
                        try:
                            filename = self.fernet.decrypt(parts[0]).decode('utf-8')
                            file_data = self.fernet.decrypt(parts[1])
                            self.root.after(0, self.save_file_dialog, filename, file_data)
                        except InvalidToken:
                            self.root.after(0, self.display_error, "⚠️ 拦截到篡改的文件数据或错误密钥！")

            except Exception:
                break
        self.root.after(0, lambda: self.status_bar.config(text="🔴 连接已断开", bg="#e74c3c"))

    def display_error(self, msg):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"\n{msg}\n", "error")
        self.chat_area.config(state='disabled')

    def lock_down(self):
        # 防暴力破解：错误3次直接断网
        self.display_error("🚨 警告：连续3次解密失败，检测到暴力破解，连接已强制断开！")
        try:
            self.conn.close()
        except:
            pass
        self.status_bar.config(text="🔴 已封锁 (防暴力破解)", bg="#e74c3c")
        self.send_btn.config(state=tk.DISABLED)
        self.file_btn.config(state=tk.DISABLED)

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg: return
        self.msg_entry.delete(0, tk.END)
        try:
            enc_msg = self.fernet.encrypt(msg.encode('utf-8'))
            self.conn.sendall(b"TEXT:" + enc_msg + b'\n')
            self.display_message(msg, "me")
        except Exception:
            messagebox.showerror("发送失败", "连接已断开")

    def send_file(self):
        filepath = filedialog.askopenfilename(title="选择要加密发送的文件")
        if not filepath: return
        try:
            filename = os.path.basename(filepath)
            with open(filepath, 'rb') as f:
                file_data = f.read()

            # 加密文件名和文件内容，并拼接发送
            enc_filename = self.fernet.encrypt(filename.encode('utf-8'))
            enc_data = self.fernet.encrypt(file_data)
            self.conn.sendall(b"FILE:" + enc_filename + b":" + enc_data + b'\n')

            self.display_message(f"[已发送安全文件]: {filename}", "me")
        except Exception as e:
            messagebox.showerror("错误", f"发送文件失败: {e}")

    def save_file_dialog(self, filename, file_data):
        save_path = filedialog.asksaveasfilename(initialfile=filename, title="保存解密后的文件")
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(file_data)
            self.display_message(f"[已接收并解密文件]: {filename}", "other")

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