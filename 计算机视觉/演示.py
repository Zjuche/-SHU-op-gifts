def main():
    a = int(input("请输入第一个整数"))
    b = int(input("请输入第二个整数"))

    # 直接计算结果并输出
    print(f"和是{a + b}")
    print(f"差是{a - b}")
    print(f"积是{a * b}")

    # 使用三元表达式处理除法
    print("除数不能为零" if b == 0 else f"商是{a / b}")


if __name__ == "__main__":
    main()