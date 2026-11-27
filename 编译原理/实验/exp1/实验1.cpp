#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <cctype>
#include <set>

using namespace std;

// PL/0 关键字集合（不区分大小写，用小写存储）
const set<string> keywords = {
    "const", "var", "procedure", "begin", "end",
    "if", "then", "while", "do", "call", "odd",
    "read", "write"
};

// 判断字符是否为字母
bool isLetter(char ch) {
    return (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z');
}

// 判断字符是否为数字
bool isDigit(char ch) {
    return ch >= '0' && ch <= '9';
}

// 将字符串转为小写
string toLower(const string &s) {
    string res = s;
    for (char &c : res) {
        if (c >= 'A' && c <= 'Z')
            c = c - 'A' + 'a';
    }
    return res;
}

int main() {
    // 输入输出文件名（可根据需要修改）
    string inputFileName = "input.pl0";
    string outputFileName = "output.txt";

    // 读取源文件
    ifstream inFile(inputFileName);
    if (!inFile) {
        cerr << "无法打开输入文件: " << inputFileName << endl;
        return 1;
    }

    // 将整个文件读入一个字符串
    string source;
    char ch;
    while (inFile.get(ch)) {
        source += ch;
    }
    inFile.close();

    // 统计标识符
    unordered_map<string, int> countMap;     // 标识符（小写）-> 出现次数
    vector<string> orderList;                // 按第一次出现顺序存储的小写标识符

    size_t i = 0;
    size_t len = source.length();

    while (i < len) {
        // 跳过非字母字符（数字开头的 token 不是标识符，直接跳过）
        if (!isLetter(source[i])) {
            ++i;
            continue;
        }

        // 提取一个字母开头的完整 token
        size_t start = i;
        while (i < len && (isLetter(source[i]) || isDigit(source[i]))) {
            ++i;
        }
        string token = source.substr(start, i - start);

        // 转为小写用于比较和存储
        string lowerToken = toLower(token);

        // 如果不是关键字，则视为标识符
        if (keywords.find(lowerToken) == keywords.end()) {
            // 如果是第一次出现，记录到顺序列表
            if (countMap.find(lowerToken) == countMap.end()) {
                orderList.push_back(lowerToken);
            }
            // 次数加一
            countMap[lowerToken]++;
        }
        // 若是关键字，直接忽略，不统计
    }

    // 输出结果到文件
    ofstream outFile(outputFileName);
    if (!outFile) {
        cerr << "无法创建输出文件: " << outputFileName << endl;
        return 1;
    }

    for (const string &id : orderList) {
        outFile << "(" << id << ": " << countMap[id] << ")" << endl;
    }
    outFile.close();

    cout << "统计完成，结果已保存至 " << outputFileName << endl;
    return 0;
}
