#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <openssl/evp.h>
#include <sys/stat.h>
#include <time.h>

#define PORT 5000
#define MAX_LEN 2048

unsigned char aes_key[32];
int connfd;
int auth_fail_count = 0;
char log_file[256];

// 记录聊天日志
void write_chat_log(const char* direction, const char* msg) {
    FILE *fp = fopen(log_file, "a");
    if (fp) {
        time_t t = time(NULL);
        struct tm *tm = localtime(&t);
        fprintf(fp, "[%02d:%02d:%02d] %s: %s\n", tm->tm_hour, tm->tm_min, tm->tm_sec, direction, msg);
        fclose(fp);
    }
}

// AES 加密
int encrypt_data(unsigned char *plaintext, int plaintext_len, unsigned char *ciphertext) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    int len, ciphertext_len;
    EVP_EncryptInit_ex(ctx, EVP_aes_256_ecb(), NULL, aes_key, NULL);
    EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, plaintext_len);
    ciphertext_len = len;
    EVP_EncryptFinal_ex(ctx, ciphertext + len, &len);
    ciphertext_len += len;
    EVP_CIPHER_CTX_free(ctx);
    return ciphertext_len;
}

// AES 解密
int decrypt_data(unsigned char *ciphertext, int ciphertext_len, unsigned char *plaintext) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    int len, plaintext_len;
    EVP_DecryptInit_ex(ctx, EVP_aes_256_ecb(), NULL, aes_key, NULL);
    EVP_DecryptUpdate(ctx, plaintext, &len, ciphertext, ciphertext_len);
    plaintext_len = len;
    if (EVP_DecryptFinal_ex(ctx, plaintext + len, &len) <= 0) {
        EVP_CIPHER_CTX_free(ctx);
        return -1; // 密钥不对或数据被篡改
    }
    plaintext_len += len;
    plaintext[plaintext_len] = '\0';
    EVP_CIPHER_CTX_free(ctx);
    return plaintext_len;
}

// 接收线程
void *recv_thread(void *arg) {
    unsigned char buffer[MAX_LEN], decrypted[MAX_LEN];
    while (1) {
        memset(buffer, 0, MAX_LEN);
        int bytes = recv(connfd, buffer, MAX_LEN, 0);
        if (bytes <= 0) {
            printf("\n[!] 对方已断开连接。\n> ");
            break;
        }
        
        int dec_len = decrypt_data(buffer, bytes, decrypted);
        if (dec_len < 0) {
            auth_fail_count++;
            printf("\n[⚠️ 解密失败！密钥不匹配] (尝试次数: %d/3)\n> ", auth_fail_count);
            write_chat_log("系统", "解密失败，可能遭遇拦截或错误密钥");
            
            if (auth_fail_count >= 3) {
                printf("\n[🚨 防爆破触发] 连续3次错误，自动断开连接！\n");
                write_chat_log("系统", "触发防爆破机制，强制下线");
                close(connfd);
                exit(0);
            }
        } else {
            printf("\n[收到] %s\n> ", decrypted);
            write_chat_log("收到", (char*)decrypted);
        }
        fflush(stdout);
    }
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("用法: %s <server|client> <key文件>\n", argv[0]);
        return 1;
    }

    // 初始化日志
    mkdir("logs", 0777);
    time_t t = time(NULL);
    struct tm *tm = localtime(&t);
    sprintf(log_file, "logs/chat_c_%04d%02d%02d_%02d%02d%02d.txt", 
            tm->tm_year + 1900, tm->tm_mon + 1, tm->tm_mday, tm->tm_hour, tm->tm_min, tm->tm_sec);

    // 读取 32 字节 Key
    FILE *fp = fopen(argv[2], "rb");
    if (!fp) { perror("无法打开密钥文件"); return 1; }
    fread(aes_key, 1, 32, fp);
    fclose(fp);

    if (strcmp(argv[1], "server") == 0) {
        int server_fd = socket(AF_INET, SOCK_STREAM, 0);
        int opt = 1;
        setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
        struct sockaddr_in address;
        address.sin_family = AF_INET;
        address.sin_addr.s_addr = INADDR_ANY;
        address.sin_port = htons(PORT);

        bind(server_fd, (struct sockaddr *)&address, sizeof(address));
        listen(server_fd, 1);
        printf("[服务端] 监听端口 %d，等待连接...\n", PORT);
        
        connfd = accept(server_fd, NULL, NULL);
        printf("[服务端] 客户端已连接！\n");
    } else {
        connfd = socket(AF_INET, SOCK_STREAM, 0);
        struct sockaddr_in serv_addr;
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(PORT);
        inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr);
        
        if (connect(connfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
            perror("连接失败"); return 1;
        }
        printf("[客户端] 连接成功！\n");
    }

    pthread_t tid;
    pthread_create(&tid, NULL, recv_thread, NULL);

    char input[MAX_LEN];
    unsigned char ciphertext[MAX_LEN + 16];
    printf("可以开始聊天了，输入 /quit 退出。\n");
    
    while (1) {
        printf("> ");
        fflush(stdout);
        if (!fgets(input, MAX_LEN, stdin)) break;
        input[strcspn(input, "\n")] = 0;
        
        if (strcmp(input, "/quit") == 0) break;
        
        int cipher_len = encrypt_data((unsigned char *)input, strlen(input), ciphertext);
        send(connfd, ciphertext, cipher_len, 0);
        write_chat_log("发送", input);
    }

    close(connfd);
    return 0;
}
