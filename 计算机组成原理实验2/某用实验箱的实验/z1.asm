LOOP1:
输入A A,#05H
OUT输出
输入A A,#10H
L1:
减法A A,#01H
零跳转 LOOP2
跳到 L1
LOOP2:
输入A A,#04H
OUT输出
输入A A,#10H
L2:
减法A A,#01H
零跳转 LOOP3
跳到 L2
LOOP3:
输入A A,#03H
OUT输出
输入A A,#10H
L3:
减法A A,#01H
零跳转 LOOP4
跳到 L3
LOOP4:
输入A A,#02H
OUT输出
输入A A,#10H
L4:
减法A A,#01H
零跳转 LOOP5
跳到 L3
LOOP5:
输入A A,#01H
OUT输出
输入A A,#10H
L5:
减法A A,#01H
零跳转 LOOP1
跳到 L5