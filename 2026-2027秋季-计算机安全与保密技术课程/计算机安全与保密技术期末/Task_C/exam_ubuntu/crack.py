import sys

# 导入 Linux 专有的 crypt 模块，Windows 没有
try:
    import crypt
except ImportError:
    print("【错误】当前系统不支持 crypt 模块，请在 Linux / Ubuntu 下运行此脚本！")
    sys.exit(1)


def main():
    # 检查命令行参数
    if len(sys.argv) != 3:
        print("用法: python3 crack.py <shadow文件> <字典文件>")
        print("示例: python3 crack.py shadow_test.txt words.list")
        sys.exit(1)

    shadow_file = sys.argv[1]
    wordlist_file = sys.argv[2]

    # 1. 解析目标 shadow 文件
    targets = {}
    try:
        with open(shadow_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) >= 2:
                    user = parts[0]
                    pwd_hash = parts[1]
                    # 过滤掉没有密码或账号被锁定的情况（如 ! 或 * 开头）
                    if pwd_hash and not pwd_hash.startswith(('!', '*')):
                        targets[user] = pwd_hash
    except FileNotFoundError:
        print(f"错误: 找不到文件 {shadow_file}")
        sys.exit(1)

    if not targets:
        print("未在文件中找到有效且未锁定的用户账户。")
        sys.exit(0)

    print(f"[*] 成功加载目标文件，共发现 {len(targets)} 个待破解用户。")

    # 2. 加载字典文件
    try:
        with open(wordlist_file, 'r', encoding='utf-8') as f:
            words = [w.strip() for w in f if w.strip()]
    except FileNotFoundError:
        print(f"错误: 找不到字典文件 {wordlist_file}")
        sys.exit(1)

    print(f"[*] 成功加载字典文件，共 {len(words)} 个候选密码。\n")

    # 3. 开始暴力尝试（字典攻击）
    for user, pwd_hash in targets.items():
        print(f"[*] 正在尝试破解用户: {user} ...")

        # 获取哈希值的前缀（即盐值 Salt），例如 '$6$xxxxx$'
        salt = crypt.mksalt(crypt.METHOD_SHA512)  # 默认生成
        parts = pwd_hash.split('$')
        if len(parts) >= 3:
            # 提取原哈希中的盐，保证加密方式一致
            salt = f"${parts[1]}${parts[2]}"

        found = False
        for word in words:
            # 核心逻辑：用相同的盐去加密字典里的词，看是否和原哈希匹配
            if crypt.crypt(word, salt) == pwd_hash:
                print(f"  [🎉 成功] 用户 [{user}] 的密码是: {word}\n")
                found = True
                break

        if not found:
            print(f"  [❌ 失败] 字典穷尽，未能破解用户 [{user}] 的密码。\n")


if __name__ == '__main__':
    main()