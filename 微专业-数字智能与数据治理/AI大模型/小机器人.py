from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import PromptTemplate

MY_ZHIPU_API_KEY="30ba353143714ce990c3d345cb937240.ds7PR3o6qolCLAKi"

def main():
    try:
        llm=ChatZhipuAI(
           model='glm-4.5-flash',
           api_key=MY_ZHIPU_API_KEY,
           temperature=0.5
        )
        print("智谱AI（glm-4.5-flash）模型初始化成功")
    except Exception as e:
        print(f"初始化LLM过滤器：{e}")
        print("请检查：1.'pip install langchain-community zhipuai'")