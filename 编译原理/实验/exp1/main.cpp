#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <cctype>
using namespace std;

// PL/0 关键字集合（均为小写）
const string keywords[] = {
    "const", "var", "procedure", "begin", "end", "if", "then",
    "while", "do", "call", "odd", "read", "write"
};
const int KEYWORD_COUNT = 13;

bool isKeyword(const string &word) {
    string lower = word;
    for (char &c : lower) c = tolower(c);
    for (int i = 0; i < KEYWORD_COUNT; i++)
        if (lower == keywords[i]) return true;
    return false;
}

int main(int argc, char *argv[]) {
    // 输入输出文件名
    string inputFile = "input.pl0";
    string outputFile = "output.txt";
    if (argc >= 2) inputFile = argv[1];
    if (argc >= 3) outputFile = argv[2];

    ifstream fin(inputFile);
    if (!fin) {
        cerr << "无法打开输入文件: " << inputFile << endl;
        return 1;
    }

    // 存储标识符：原始形式按出现顺序保存，小写形式用于计数
    vector<string> idList;                // 第一次出现的原始形式
    unordered_map<string, int> countMap;  // 小写 → 出现次数
    unordered_map<string, int> indexMap;  // 小写 → idList 中的索引

    char ch;
    string buffer;
    bool inComment = false;

    while (fin.get(ch)) {
        if (inComment) {
            if (ch == '}') inComment = false;
            continue;
        }
        if (ch == '{') {
            inComment = true;
            continue;
        }

        if (isalpha(ch)) {
            // 标识符或关键字
            buffer.clear();
            buffer += ch;
            while (fin.get(ch) && (isalnum(ch))) {
                buffer += ch;
            }
            fin.unget();  // 多读了一个字符，退回

            if (!isKeyword(buffer)) {
                // 转为小写统计
                string lower = buffer;
                for (char &c : lower) c = tolower(c);

                countMap[lower]++;

                if (indexMap.find(lower) == indexMap.end()) {
                    // 第一次出现，记录原始形式
                    indexMap[lower] = idList.size();
                    idList.push_back(buffer);
                }
            }
        }
        else if (isdigit(ch)) {
            // 跳过数字
            while (fin.get(ch) && isdigit(ch));
            fin.unget();
        }
        // 其他字符（运算符、分隔符等）直接忽略
    }
    fin.close();

    // 输出结果
    ofstream fout(outputFile);
    if (!fout) {
        cerr << "无法创建输出文件: " << outputFile << endl;
        return 1;
    }

    for (const string &id : idList) {
        string lower = id;
        for (char &c : lower) c = tolower(c);
        fout << "(" << id << ": " << countMap[lower] << ")" << endl;
    }
    fout.close();

    cout << "统计完成，结果已写入 " << outputFile << endl;
    return 0;
}
