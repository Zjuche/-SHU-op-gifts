#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <cctype>
#include <cstdio>
#include <cstdlib>

// 词法单元类型枚举
enum TokenType {
    TOKEN_IDENT,
    TOKEN_NUMBER,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_TIMES,
    TOKEN_DIVIDE,
    TOKEN_LPAREN,
    TOKEN_RPAREN,
    TOKEN_UNKNOWN,
    TOKEN_END
};

// 词法单元结构
struct Token {
    TokenType type;
    std::string lexeme;
};

// 类型名到枚举的映射
std::map<std::string, TokenType> typeMap;

// 整数转字符串（C++98兼容） - 定义在readTokens之前
std::string intToString(int n) {
    char buf[32];
    sprintf(buf, "%d", n);
    return std::string(buf);
}

// 初始化映射表
void initTypeMap() {
    typeMap["div"] = TOKEN_DIVIDE;
	typeMap["ident"] = TOKEN_IDENT;
    typeMap["number"] = TOKEN_NUMBER;
    typeMap["plus"] = TOKEN_PLUS;
    typeMap["minus"] = TOKEN_MINUS;
    typeMap["times"] = TOKEN_TIMES;
    typeMap["slash"] = TOKEN_DIVIDE;
    typeMap["lparen"] = TOKEN_LPAREN;
    typeMap["rparen"] = TOKEN_RPAREN;
}

// 将字符串转换为TokenType
TokenType strToTokenType(const std::string& str) {
    std::map<std::string, TokenType>::iterator it = typeMap.find(str);
    if (it != typeMap.end())
        return it->second;
    return TOKEN_UNKNOWN;
}

// 读取二元组文件，解析为Token列表
bool readTokens(const std::string& filename, std::vector<Token>& tokens, std::string& errorMsg) {
    tokens.clear();
    std::ifstream file(filename.c_str());
    if (!file.is_open()) {
        errorMsg = "无法打开文件";
        return false;
    }

    std::string line;
    int lineNum = 0;
    while (std::getline(file, line)) {
        lineNum++;
        // 跳过空行
        if (line.empty()) continue;
        // 去除首尾空白
        size_t start = line.find_first_not_of(" \t");
        if (start == std::string::npos) continue;
        size_t end = line.find_last_not_of(" \t");
        line = line.substr(start, end - start + 1);

        // 检查格式 (type,value)
        if (line.size() < 3 || line[0] != '(' || line[line.size()-1] != ')') {
            errorMsg = "第" + intToString(lineNum) + "行格式错误，缺少括号: " + line;
            return false;
        }
        line = line.substr(1, line.size() - 2);
        size_t comma = line.find(',');
        if (comma == std::string::npos) {
            errorMsg = "第" + intToString(lineNum) + "行缺少逗号: " + line;
            return false;
        }
        std::string typeStr = line.substr(0, comma);
        std::string lexeme = line.substr(comma + 1);
        // 去除空白
        typeStr.erase(0, typeStr.find_first_not_of(" \t"));
        typeStr.erase(typeStr.find_last_not_of(" \t") + 1);
        lexeme.erase(0, lexeme.find_first_not_of(" \t"));
        lexeme.erase(lexeme.find_last_not_of(" \t") + 1);

        TokenType tt = strToTokenType(typeStr);
        if (tt == TOKEN_UNKNOWN) {
            errorMsg = "第" + intToString(lineNum) + "行未知token类型: " + typeStr;
            return false;
        }
        Token tok = {tt, lexeme};
        tokens.push_back(tok);
    }
    file.close();
    return true;
}

// 语法分析器类（递归下降）
class Parser {
private:
    std::vector<Token> tokens;
    size_t pos;
    bool errorFlag;
    std::string errorMsg;

    Token currentToken() const {
        if (pos < tokens.size())
            return tokens[pos];
        Token end = {TOKEN_END, "EOF"};
        return end;
    }

    void consume() {
        if (pos < tokens.size())
            ++pos;
    }

    void match(TokenType expected) {
        Token cur = currentToken();
        if (cur.type == expected) {
            consume();
        } else {
            std::string expectedStr;
            for (std::map<std::string, TokenType>::iterator it = typeMap.begin(); it != typeMap.end(); ++it) {
                if (it->second == expected) {
                    expectedStr = it->first;
                    break;
                }
            }
            error("期望 '" + expectedStr + "' 但遇到 '" + cur.lexeme + "'");
        }
    }

    void error(const std::string& msg) {
        if (!errorFlag) {
            errorFlag = true;
            errorMsg = msg;
        }
    }

    void parseFactor() {
        if (errorFlag) return;
        Token cur = currentToken();
        if (cur.type == TOKEN_IDENT) {
            consume();
        } else if (cur.type == TOKEN_NUMBER) {
            consume();
        } else if (cur.type == TOKEN_LPAREN) {
            consume();
            parseExpression();
            if (!errorFlag) match(TOKEN_RPAREN);
        } else {
            error("因子应以标识符、数字或 '(' 开头，但遇到 '" + cur.lexeme + "' (类型码=" + intToString(cur.type) + ")");
        }
    }

    void parseTerm() {
        if (errorFlag) return;
        parseFactor();
        if (errorFlag) return;
        while (true) {
            Token cur = currentToken();
            if (cur.type == TOKEN_TIMES || cur.type == TOKEN_DIVIDE) {
                consume();
                parseFactor();
                if (errorFlag) return;
            } else {
                break;
            }
        }
    }

    void parseExpression() {
        if (errorFlag) return;
        Token cur = currentToken();
        if (cur.type == TOKEN_PLUS || cur.type == TOKEN_MINUS) {
            consume();
        }
        parseTerm();
        if (errorFlag) return;
        while (true) {
            cur = currentToken();
            if (cur.type == TOKEN_PLUS || cur.type == TOKEN_MINUS) {
                consume();
                parseTerm();
                if (errorFlag) return;
            } else {
                break;
            }
        }
    }

public:
    Parser(const std::vector<Token>& tokenList) : tokens(tokenList), pos(0), errorFlag(false) {}

    bool parse() {
        parseExpression();
        if (!errorFlag && pos != tokens.size()) {
            Token extra = currentToken();
            error("表达式结束后存在多余内容 '" + extra.lexeme + "'");
        }
        return !errorFlag;
    }

    std::string getErrorMsg() const {
        return errorMsg;
    }
};

// 测试单个文件
void testFile(const std::string& filename) {
    std::cout << "文件: " << filename << std::endl;
    std::vector<Token> tokens;
    std::string errorMsg;
    if (!readTokens(filename, tokens, errorMsg)) {
        std::cout << "  词法错误: " << errorMsg << std::endl << std::endl;
        return;
    }
    if (tokens.empty()) {
        std::cout << "  错误: 没有有效的token输入" << std::endl << std::endl;
        return;
    }
    Parser parser(tokens);
    bool ok = parser.parse();
    if (ok) {
        std::cout << "  语法正确" << std::endl;
    } else {
        std::cout << "  语法错误: " << parser.getErrorMsg() << std::endl;
    }
    std::cout << std::endl;
}

// 主函数
int main(int argc, char* argv[]) {
    initTypeMap();

    std::vector<std::string> testFiles;
    if (argc > 1) {
        for (int i = 1; i < argc; ++i) {
            testFiles.push_back(argv[i]);
        }
    } else {
        // 默认测试 input1.txt 到 input10.txt
        for (int i = 1; i <= 10; ++i) {
            testFiles.push_back("input" + intToString(i) + ".txt");
        }
    }

    for (size_t i = 0; i < testFiles.size(); ++i) {
        testFile(testFiles[i]);
    }
	system("pause");
    return 0;
}
