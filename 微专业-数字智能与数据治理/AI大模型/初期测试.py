from langchain_core.prompts import PromptTemplate

template="你是一个{rule}，请用一句话介绍你自己"
prompt=PromptTemplate.from_template(template)

result=prompt.format(rule="ai学习")

print("---测试成功---")
print(result)