#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <crypt.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <stdarg.h> // 支持 va_list

FILE *log_fp = NULL;

// 修复：避免连续使用 va_list 导致越界段错误
void log_msg(const char *format, ...) {
    char buffer[2048]; // 分配足够大的缓冲区
    va_list args;
    
    va_start(args, format);
    // 将可变参数格式化并存入 buffer，防止后续重复消耗指针
    vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);

    // 打印到屏幕
    printf("%s", buffer);
    
    // 打印到日志文件
    if (log_fp) {
        fprintf(log_fp, "%s", buffer);
        fflush(log_fp);
    }
}

// 提取哈希中的 Salt (例如从 $6$xxxx$yyy 提取 $6$xxxx$)
void get_salt(const char *hash, char *salt) {
    const char *p1 = strchr(hash, '$');
    if (!p1) return;
    const char *p2 = strchr(p1 + 1, '$');
    if (!p2) return;
    const char *p3 = strchr(p2 + 1, '$');
    if (!p3) return;
    int len = p3 - hash + 1;
    if (len >= 128) return; // 防止越界
    strncpy(salt, hash, len);
    salt[len] = '\0';
}

// 暴力穷举 (深度优先搜索)
int brute_force(const char *hash, const char *salt, char *found_word, int max_len) {
    char current[10] = {0};
    
    // 递归函数
    int dfs(int depth) {
        if (depth > 0) {
            if (strcmp(crypt(current, salt), hash) == 0) {
                strcpy(found_word, current);
                return 1;
            }
        }
        if (depth == max_len) return 0;
        
        for (char c = 'a'; c <= 'z'; c++) {
            current[depth] = c;
            current[depth + 1] = '\0';
            if (dfs(depth + 1)) return 1;
        }
        return 0;
    }
    
    return dfs(0);
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("用法: %s <shadow文件> <字典文件>\n", argv[0]);
        printf("示例: %s ~/Desktop/shadow.txt words.list\n", argv[0]);
        return 1;
    }

    // 1. 初始化日志
    mkdir("logs", 0777);
    time_t t = time(NULL);
    struct tm *tm = localtime(&t);
    char log_path[256];
    strftime(log_path, sizeof(log_path), "logs/crack_c_log_%Y%m%d_%H%M%S.txt", tm);
    log_fp = fopen(log_path, "w");
    if (!log_fp) {
        printf("[-] 无法创建日志文件，请检查权限。\n");
    }
    
    log_msg("=== C语言终极破解日志 ===\n");

    // 2. 读取目标哈希 (默认找 seed 用户)
    char target_user[64] = "seed";
    char target_hash[256] = {0};
    FILE *sfp = fopen(argv[1], "r");
    if (!sfp) {
        log_msg("[-] 无法打开 shadow 文件\n");
        return 1;
    }
    
    char line[512];
    while (fgets(line, sizeof(line), sfp)) {
        char user[128], hash[256];
        if (sscanf(line, "%[^:]:%[^:]", user, hash) == 2) {
            if (strcmp(user, target_user) == 0) {
                strcpy(target_hash, hash);
                break;
            }
        }
    }
    fclose(sfp);
    
    if (strlen(target_hash) == 0) {
        log_msg("[-] 未在文件中找到用户 %s 的哈希\n", target_user);
        return 1;
    }
    log_msg("[*] 成功获取目标 [%s] 的哈希: %s\n", target_user, target_hash);

    // 3. 提取 Salt
    char salt[128] = {0};
    get_salt(target_hash, salt);
    log_msg("[*] 提取盐值 (Salt): %s\n", salt);

    char found_pwd[128] = {0};

    // 4. 阶段一：字典攻击
    log_msg("[*] 阶段一：开始字典攻击...\n");
    FILE *dfp = fopen(argv[2], "r");
    if (dfp) {
        char word[128];
        while (fgets(word, sizeof(word), dfp)) {
            word[strcspn(word, "\n")] = 0;
            if (strcmp(crypt(word, salt), target_hash) == 0) {
                strcpy(found_pwd, word);
                break;
            }
        }
        fclose(dfp);
    }

    // 5. 阶段二：暴力穷举 (1-4位)
    if (strlen(found_pwd) == 0) {
        log_msg("[-] 字典未命中。\n");
        log_msg("[*] 阶段二：开始 1-4 位小写字母暴力穷举...\n");
        log_msg("[*] 正在计算中，请稍候...\n");
        
        if (brute_force(target_hash, salt, found_pwd, 4)) {
            // 成功找到
        }
    }

    // 6. 输出结果
    log_msg("\n========================================\n");
    if (strlen(found_pwd) > 0) {
        log_msg("[🎉 成功] 账号 [%s] 的密码是: %s\n", target_user, found_pwd);
    } else {
        log_msg("[❌ 失败] 未能破解出密码。\n");
    }
    log_msg("========================================\n");
    log_msg("[*] 日志已保存至: %s\n", log_path);

    if (log_fp) fclose(log_fp);
    return 0;
}
