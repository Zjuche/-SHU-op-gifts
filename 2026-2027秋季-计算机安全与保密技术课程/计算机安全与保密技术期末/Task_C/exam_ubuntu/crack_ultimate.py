import crypt
import itertools
import string
import sys
import time
import os
import datetime

# 🌟 新增：日志记录函数
def write_log(msg, log_file):
    print(msg)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def load_target(shadow_file, target_user):
    try:
        with open(shadow_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) >= 2 and parts[0] == target_user:
                    if parts[1] and not parts[1].startswith(('!', '*')):
                        return parts[1]
        return None
    except Exception:
        return None

def extract_salt(pwd_hash):
    parts = pwd_hash.split('$')
    if len(parts) >= 3:
        return f"${parts[1]}${parts[2]}"
    return crypt.mksalt(crypt.METHOD_SHA512)

def dictionary_attack(pwd_hash, salt, wordlist_file, log_file):
    write_log(f"[*] 阶段一：开始字典攻击 (目标字典: {wordlist_file})", log_file)
    try:
        with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
            words = [w.strip() for w in f if w.strip()]
    except FileNotFoundError:
        write_log(f"[-] 找不到字典文件 {wordlist_file}，跳过字典攻击。", log_file)
        return None

    for word in words:
        if crypt.crypt(word, salt) == pwd_hash:
            return word
    return None

def brute_force_attack(pwd_hash, salt, log_file, max_length=4):
    write_log(f"[*] 阶段二：字典未命中，启动暴力穷举 (1 - {max_length} 位小写字母)", log_file)
    chars = string.ascii_lowercase 
    
    start_time = time.time()
    count = 0
    
    for length in range(1, max_length + 1):
        write_log(f"  [-] 正在尝试长度为 {length} 的密码组合...", log_file)
        for combo in itertools.product(chars, repeat=length):
            guess = "".join(combo)
            count += 1
            if crypt.crypt(guess, salt) == pwd_hash:
                return guess
            
            if count % 50000 == 0:
                elapsed = time.time() - start_time
                print(f"      已尝试 {count} 次, 耗时 {elapsed:.1f} 秒...", end='\r')
                
    return None

def main():
    if len(sys.argv) != 3:
        print("用法: python3 crack_ultimate.py <shadow文件> <字典文件>")
        sys.exit(1)

    shadow_file = sys.argv[1]
    wordlist_file = sys.argv[2]
    target_user = "seed" 
    
    # 🌟 新增：创建 logs 文件夹
    if not os.path.exists("logs"):
        os.makedirs("logs")
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join("logs", f"ultimate_log_{now}.txt")
    write_log(f"=== 终极破解日志 {now} ===", log_file)

    write_log(f"[*] 正在加载目标用户: {target_user}", log_file)
    pwd_hash = load_target(shadow_file, target_user)
    
    if not pwd_hash:
        write_log(f"[-] 未能找到用户 {target_user} 的哈希，或者账号被锁定。", log_file)
        sys.exit(1)
        
    write_log(f"[*] 成功获取哈希: {pwd_hash}", log_file)
    salt = extract_salt(pwd_hash)
    
    start_time = time.time()
    
    password = dictionary_attack(pwd_hash, salt, wordlist_file, log_file)
    
    if not password:
        write_log("[-] 字典攻击结束，未能匹配。", log_file)
        password = brute_force_attack(pwd_hash, salt, log_file, max_length=4)
    
    total_time = time.time() - start_time
    
    write_log("\n" + "="*40, log_file)
    if password:
        write_log(f"[🎉 成功] 账号 [{target_user}] 的密码是: {password}", log_file)
        write_log(f"[⚡ 耗时] 总共用时: {total_time:.2f} 秒", log_file)
    else:
        write_log(f"[❌ 失败] 未能破解出密码 (超出了设定的穷举范围)。", log_file)
    write_log("="*40, log_file)
    write_log(f"[*] 详细日志已保存至: {os.path.abspath(log_file)}", log_file)

if __name__ == '__main__':
    main()
