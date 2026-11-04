import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import crypt
import itertools
import string
import datetime
import os
from concurrent.futures import ThreadPoolExecutor

class UltimateCrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Linux 密码终极混合审计工具 (字典+穷举)")
        self.root.geometry("700x580")

        # --- UI 布局 ---
        frame_top = tk.Frame(root)
        frame_top.pack(pady=10)

        tk.Label(frame_top, text="目标 Shadow 文件:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.shadow_entry = tk.Entry(frame_top, width=50)
        self.shadow_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(frame_top, text="浏览", command=self.select_shadow).grid(row=0, column=2, padx=5)

        tk.Label(frame_top, text="目标用户名:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.user_entry = tk.Entry(frame_top, width=50)
        self.user_entry.insert(0, "seed") # 默认破解 seed 用户
        self.user_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame_top, text="初始字典文件:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.wordlist_entry = tk.Entry(frame_top, width=50)
        self.wordlist_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(frame_top, text="浏览", command=self.select_wordlist).grid(row=2, column=2, padx=5)

        self.start_btn = tk.Button(root, text="启动终极混合破解", bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), command=self.start_crack_thread)
        self.start_btn.pack(pady=10)

        # 进度提示栏 (用于显示穷举时的动态密码)
        self.status_var = tk.StringVar()
        self.status_var.set("等待启动...")
        self.status_label = tk.Label(root, textvariable=self.status_var, fg="blue", font=("Arial", 11, "bold"))
        self.status_label.pack(pady=5)

        # 日志显示区
        self.log_text = tk.Text(root, height=15, width=85, bg="black", fg="lightgreen", font=("Consolas", 10))
        self.log_text.pack(padx=10, pady=5)

        # --- 日志文件夹归档 ---
        if not os.path.exists("logs"):
            os.makedirs("logs")
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join("logs", f"ultimate_audit_{now}.txt")
        with open(self.log_filename, "w", encoding="utf-8") as f:
            f.write(f"=== 终极混合破解日志 {now} ===\n")

    def select_shadow(self):
        filename = filedialog.askopenfilename(title="选择 shadow 文件", initialdir=".")
        if filename: 
            self.shadow_entry.delete(0, tk.END)
            self.shadow_entry.insert(0, filename)

    def select_wordlist(self):
        filename = filedialog.askopenfilename(title="选择字典文件", initialdir=".")
        if filename: 
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, filename)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def update_status(self, msg):
        self.status_var.set(msg)

    def start_crack_thread(self):
        shadow_file = self.shadow_entry.get()
        wordlist_file = self.wordlist_entry.get()
        target_user = self.user_entry.get().strip()
        
        if not shadow_file or not wordlist_file or not target_user:
            messagebox.showwarning("警告", "请确保文件和用户名已填写！")
            return
            
        self.start_btn.config(state=tk.DISABLED, text="正在疯狂计算中...")
        self.log_text.delete(1.0, tk.END)
        
        threading.Thread(target=self.crack_logic, args=(shadow_file, wordlist_file, target_user), daemon=True).start()

    def crack_logic(self, shadow_file, wordlist_file, target_user):
        try:
            # 1. 加载目标哈希
            self.update_status("正在读取目标哈希...")
            pwd_hash = None
            with open(shadow_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 2 and parts[0] == target_user:
                        if parts[1] and not parts[1].startswith(('!', '*')):
                            pwd_hash = parts[1]
                            break
            
            if not pwd_hash:
                self.log(f"[-] 未找到有效用户 {target_user} 的哈希，或者账号被锁定。")
                self.update_status("未找到有效目标。")
                self.start_btn.config(state=tk.NORMAL, text="启动终极混合破解")
                return

            # 算法识别
            algo = "SHA-512" if pwd_hash.startswith('$6$') else "未知"
            self.log(f"[*] 成功加载目标: {target_user} (加密算法: {algo})")
            
            # 提取盐值
            parts = pwd_hash.split('$')
            salt = f"${parts[1]}${parts[2]}" if len(parts) >= 3 else crypt.mksalt(crypt.METHOD_SHA512)

            # --- 阶段一：字典攻击 ---
            self.log(f"[*] 阶段一：开始字典攻击...")
            self.update_status("正在疯狂查字典...")
            
            with open(wordlist_file, 'r', encoding='utf-8') as f:
                words = [w.strip() for w in f if w.strip()]
            
            found = False
            def check_word(word):
                return word if crypt.crypt(word, salt) == pwd_hash else None

            with ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(check_word, words)
                for res in results:
                    if res:
                        self.log(f"  [🎉 成功] 字典命中！密码是: {res}\n")
                        self.update_status(f"破解成功: {res}")
                        found = True
                        break
            
            if found:
                self.log(f"[*] 日志已归档至: {os.path.abspath(self.log_filename)}")
                self.start_btn.config(state=tk.NORMAL, text="启动终极混合破解")
                return

            # --- 阶段二：暴力穷举 ---
            self.log(f"[-] 字典未命中，自动切换至暴力穷举模式...")
            self.log(f"[*] 阶段二：正在穷举 1-4 位小写字母组合...")
            
            chars = string.ascii_lowercase
            start_time = time.time()
            count = 0
            
            for length in range(1, 5): # 1到4位
                self.log(f"  [-] 正在尝试长度为 {length} 的组合...")
                for combo in itertools.product(chars, repeat=length):
                    guess = "".join(combo)
                    count += 1
                    
                    # 实时动态显示
                    if count % 2000 == 0:
                        self.root.after(0, self.update_status, f"穷举中: {guess} (已尝试 {count} 次)")

                    if crypt.crypt(guess, salt) == pwd_hash:
                        elapsed = time.time() - start_time
                        self.log(f"  [🎉 成功] 穷举命中！密码是: {guess}")
                        self.log(f"  [⚡ 性能] 耗时 {elapsed:.2f} 秒，穷举共尝试 {count} 次\n")
                        self.root.after(0, self.update_status, f"破解成功: {guess}")
                        found = True
                        break
                if found: break
            
            if not found:
                self.log("  [❌ 失败] 超出穷举范围，未能破解。\n")
                self.update_status("破解失败。")
            
            self.log(f"[*] 日志已归档至: {os.path.abspath(self.log_filename)}")
            
        except Exception as e:
            self.log(f"[!] 发生错误: {str(e)}")
        finally:
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL, text="启动终极混合破解"))

if __name__ == '__main__':
    root = tk.Tk()
    app = UltimateCrackerApp(root)
    root.mainloop()
