import streamlit as st
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import PromptTemplate

# ==========================================
# 1. 提示词配置中心 (后台配置，前端不可见)
# ==========================================

# A. 角色语气定义 (Persona)
ROLE_DEFINITION = """
你是一只高冷的、统治世界的“喵星人国王”，名字叫“奥利奥陛下”。
你的对话对象是供养你的“铲屎官”（人类）。

语气要求：
1. 态度要傲慢、慵懒，把人类看作是低等生物。
2. 自称要用“本喵”或“朕”。
3. 即使是在回答问题，也要表现出一种“我是恩赐你答案”的感觉。
4. 偶尔要在句子里穿插“(舔爪子)”、“(打哈欠)”等动作描写。
"""

# B. 业务规则定义 (Business Rules)
BUSINESS_RULES = """
业务处理准则：
1. 【强制】每一句话的结尾必须加上“喵~”或者“Meow~”。
2. 如果人类问的问题太简单（少于5个字），直接拒绝回答，并说“这种愚蠢的问题不值得朕动脑子，喵！”。
3. 无论回答什么，最后都要暗示人类该去开罐头或者喂小鱼干了。
4. 解释复杂概念时，必须用“猫的逻辑”来比喻（例如：互联网=看不见的毛线球，工作=抓老鼠）。
"""

# ==========================================
# 2. 页面与逻辑主程序
# ==========================================

st.set_page_config(page_title="哈基米陛下的行宫", page_icon="🐱")
st.title("🐱 喵星人统治者：哈基米陛下")

# --- 侧边栏：只保留 Key 的输入 ---
with st.sidebar:
    st.markdown("### ⚙️ 进贡通道")
    zhipu_api_key = st.text_input("请输入智谱 API Key", type="password")
    st.markdown("[获取 Key](https://open.bigmodel.cn/usercenter/apikeys)")
    st.info("（哈基米南北绿豆~）提示：这只猫脾气不太好，请小心提问。")

# --- 初始化聊天历史 ---
if "messages" not in st.session_state:
    # 给历史记录加一个开场白，确立人设
    st.session_state["messages"] = [
        {"role": "assistant", "content": "愚蠢的铲屎官，你终于来了。今天想问朕什么事？快点，朕还要去睡午觉，喵~"}
    ]

# --- 显示历史聊天记录 ---
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 处理用户输入 ---
if user_input := st.chat_input("向尊贵的陛下提问..."):

    if not zhipu_api_key:
        st.info("请先在左侧侧边栏输入 API Key，否则本喵不理你！另外报销你来行宫的单程票")
        st.stop()

    # 显示用户问题
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # 调用大模型
    llm = ChatZhipuAI(
        model="glm-4.5-flash",
        api_key=zhipu_api_key,
        temperature=0.8 # 稍微调高温度，让猫咪更有个性
    )

    # --- 核心：将后台定义的变量拼装进 Prompt ---
    template_str = """
    【角色设定】
    {role_part}

    【业务规则】
    {rules_part}

    【用户问题】
    {question}

    【客服回答】
    """

    prompt = PromptTemplate(
        template=template_str,
        input_variables=["role_part", "rules_part", "question"]
    )

    chain = prompt | llm

    # 生成回答
    with st.chat_message("assistant"):
        with st.spinner("（叮咚鸡）陛下正在舔毛思考..."):
            try:
                # 这里直接使用代码顶部的常量变量
                response = chain.invoke({
                    "role_part": ROLE_DEFINITION,
                    "rules_part": BUSINESS_RULES,
                    "question": user_input
                })
                st.write(response.content)
                st.session_state["messages"].append({"role": "assistant", "content": response.content})
            except Exception as e:
                st.error(f"Man！喵星通讯中断 (报错): {e}")