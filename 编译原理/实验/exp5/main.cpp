//
//  main.cpp
//  bianyi5
//
//  Created by 何雅祺 on 2026/5/22.
//  修改为 C++98 兼容版本
//

#include <iostream>
#include <vector>
#include <string>
#include <cctype>
#include <fstream>
#include <sstream>      // 用于 stringstream

using namespace std;

string token;
string input_str;
int idx = 0;
int temp_cnt = 1;

struct Quad {
    string op, arg1, arg2, res;
};
vector<Quad> quads;

// 将整数转换为字符串（C++98 中替代 to_string）
string intToString(int n) {
    stringstream ss;
    ss << n;
    return ss.str();
}

// 词法分析
void getToken() {
    token = "";
    while (idx < input_str.size() && isspace(input_str[idx])) idx++;
    if (idx >= input_str.size()) {
        token = "#";
        return;
    }
    char ch = input_str[idx];
    if (isalpha(ch) || isdigit(ch)) {
        while (isalpha(ch) || isdigit(ch)) {
            token += ch;
            idx++;
            if (idx >= input_str.size()) break;
            ch = input_str[idx];
        }
    } else {
        token = ch;
        idx++;
    }
}

// 生成临时变量
string newTemp() {
    return "t" + intToString(temp_cnt++);
}

// 生成四元式
void gen(string op, string a1, string a2, string r) {
    Quad q;
    q.op = op; q.arg1 = a1; q.arg2 = a2; q.res = r;
    quads.push_back(q);
}

// 语法分析声明
string expr();
string term();
string factor();

string expr() {
    string e = term();
    while (token == "+" || token == "-") {
        string op = token;
        getToken();
        string t = term();
        string tmp = newTemp();
        gen(op, e, t, tmp);
        e = tmp;
    }
    return e;
}

string term() {
    string t = factor();
    while (token == "*" || token == "/") {
        string op = token;
        getToken();
        string f = factor();
        string tmp = newTemp();
        gen(op, t, f, tmp);
        t = tmp;
    }
    return t;
}

string factor() {
    string f;
    if (isalpha(token[0]) || isdigit(token[0])) {
        f = token;
        getToken();
    } else if (token == "(") {
        getToken();
        f = expr();
        if (token == ")") getToken();
        else { cout << "语法错误：缺右括号\n"; exit(1); }
    } else {
        cout << "语法错误：无效因子\n"; exit(1);
    }
    return f;
}

// 读入单个测试文件
string readFile(const string& fname) {
    // C++98 中 ifstream 构造函数需要 const char*
    ifstream fin(fname.c_str());
    if (!fin) {
        cout << "无法打开文件：" << fname << endl;
        exit(1);
    }
    string s, line;
    while (getline(fin, line)) s += line;
    fin.close();
    return s;
}

// 输出四元式到对应文件
void writeFile(const string& fname) {
    // C++98 中 ofstream 构造函数需要 const char*
    ofstream fout(fname.c_str());
    // 使用传统 for 循环（C++98 不支持范围 for）
    for (size_t i = 0; i < quads.size(); ++i) {
        const Quad& q = quads[i];
        fout << "( " << q.op << ", " << q.arg1 << ", " << q.arg2 << ", " << q.res << " )" << endl;
    }
    fout.close();
}

// 重置全局变量，用于下一组测试
void reset() {
    idx = 0;
    temp_cnt = 1;
    quads.clear();
    token = "";
}

int main() {
    // 自动处理 1~10 号用例
    for (int i = 1; i <= 10; ++i) {
        string inFile = "in" + intToString(i) + ".txt";
        string outFile = "out" + intToString(i) + ".txt";

        reset();
        input_str = readFile(inFile);
        getToken();
        expr();
        writeFile(outFile);

        cout << "已处理：" << inFile << " -> " << outFile << endl;
    }
    cout << "\n10组测试用例全部处理完成！" << endl;
    return 0;
}
