import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import crypt
import datetime
import os
from concurrent.futures import ThreadPoolExecutor

class CrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Linux 密码安全审计工具 (Final 终极版)")
        self.root.geometry("680x520")

        # --- UI 布局 ---
        tk.Label(root, text="目标 Shadow 文件:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.shadow_entry = tk.Entry(root, width=55)
        self.shadow_entry.grid(row=0, column=1, padx=10, pady=5)
        tk.Button(root, text="浏览", command=self.select_shadow).grid(row=0, column=2, padx=10)

        tk.Label(root, text="字典文件:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.wordlist_entry = tk.Entry(root, width=55)
        self.wordlist_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Button(root, text="浏览", command=self.select_wordlist).grid(row=1, column=2, padx=10)

        self.start_btn = tk.Button(root, text="开始并发破解", bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), command=self.start_crack_thread)
        self.start_btn.grid(row=2, column=0, columnspan=3, pady=15)

        self.log_text = tk.Text(root, height=18, width=85, bg="black", fg="lightgreen", font=("Consolas", 10))
        self.log_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5)

        # --- 🌟 日志文件夹自动创建与归档 ---
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join("logs", f"audit_final_{now}.txt")
        
        with open(self.log_filename, "w", encoding="utf-8") as f:
            f.write(f"=== 密码安全审计日志 (Final版) {now} ===\n")

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
        """同时输出到界面和 logs 文件夹中的文件"""
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def start_crack_thread(self):
        shadow_file = self.shadow_entry.get()
        wordlist_file = self.wordlist_entry.get()
        
        if not shadow_file or not wordlist_file:
            messagebox.showwarning("警告", "请先选择文件和字典！")
            return
            
        self.start_btn.config(state=tk.DISABLED, text="正在疯狂并发中...")
        self.log_text.delete(1.0, tk.END)
        
        # 启动子线程，防止界面卡死
        threading.Thread(target=self.crack_logic, args=(shadow_file, wordlist_file), daemon=True).start()

    def crack_logic(self, shadow_file, wordlist_file):
        try:
            # 1. 加载目标
            targets = {}
            with open(shadow_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 2 and parts[1] and not parts[1].startswith(('!', '*')):
                        targets[parts[0]] = parts[1]

            # 2. 加载字典
            with open(wordlist_file, 'r', encoding='utf-8') as f:
                words = [w.strip() for w in f if w.strip()]

            self.log(f"[*] 成功加载目标文件，共发现 {len(targets)} 个待审计用户。")
            self.log(f"[*] 成功加载字典，包含 {len(words)} 个常见弱口令。\n")

            # 3. 开始破解
            for user, pwd_hash in targets.items():
                # 算法识别
                if pwd_hash.startswith('$1$'): algo, level = "MD5", "⚠️ 极度危险！"
                elif pwd_hash.startswith('$5$'): algo, level = "SHA-256", "较安全"
                elif pwd_hash.startswith('$6$'): algo, level = "SHA-512", "安全"
                else: algo, level = "未知", "未知"

                self.log(f"[*] 正在审计用户: {user}")
                self.log(f"    └─ 加密算法: {algo} ({level})")
                
                # 提取盐值 Salt
                parts = pwd_hash.split('$')
                salt = f"${parts[1]}${parts[2]}" if len(parts) >= 3 else crypt.mksalt(crypt.METHOD_SHA512)

                start_time = time.time()
                found = False
                
                # 并发校验函数
                def check_word(word):
                    if crypt.crypt(word, salt) == pwd_hash:
                        return word
                    return None

                # 利用 10 个线程并发穷举字典
                with ThreadPoolExecutor(max_workers=10) as executor:
                    results = executor.map(check_word, words)
                    for res in results:
                        if res:
                            elapsed = time.time() - start_time
                            speed = len(words) / elapsed if elapsed > 0 else 0
                            self.log(f"  [🎉 成功] 密码是: {res}")
                            self.log(f"  [⚡ 性能] 耗时 {elapsed:.2f} 秒，并发速度约 {int(speed)} 次/秒\n")
                            found = True
                            break
                
                if not found:
                    self.log(f"  [❌ 失败] 字典穷尽，未发现该用户的弱口令。\n")

            self.log(f"=== 审计结束 ===")
            self.log(f"[*] 详细日志已归档至: {os.path.abspath(self.log_filename)}")

        except Exception as e:
            self.log(f"[!] 发生错误: {str(e)}")
        finally:
            self.start_btn.config(state=tk.NORMAL, text="开始并发破解")

if __name__ == '__main__':
    root = tk.Tk()
    app = CrackerApp(root)
    root.mainloop()
