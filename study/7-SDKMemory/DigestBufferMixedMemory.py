import os
from typing import Any
from click import prompt
import dotenv
from openai import OpenAI


dotenv.load_dotenv()


class ConversationSummaryBufferMemory:
    """摘要缓冲混合记忆类"""

    def __init__(
        self, summary: str = "", chat_histories: list = None, max_tokens: int = 300
    ):
        self.summary = summary
        self.chat_histories = [] if chat_histories is None else chat_histories
        self.max_tokens = max_tokens
        self._client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_API_BASE"),
        )

    @classmethod
    def get_num_tokens(cls, query: str) -> int:
        """计算当前传入的token数量"""
        return len(query)

    def save_context(self, human_query: str, ai_response: str) -> None:
        """保存传入的新一次对话信息"""
        self.chat_histories.append(
            {
                "human": human_query,
                "ai": ai_response,
            }
        )

        buffer_string = self.get_buffer_string()  # 获取历史对话

        tokens = self.get_num_tokens(buffer_string)  # 获取token数量

        if tokens > self.max_tokens:
            first_chat = self.chat_histories[0]
            print("删除的对话: ", first_chat)
            self.summary = self.summary_text(
                self.summary, f"Human: {first_chat['human']}\nAI: {first_chat['ai']}"
            )
            print("新的摘要: ", self.summary)
            del self.chat_histories[0]

    def get_buffer_string(self) -> str:
        """将历史对话转换为字符串"""
        buffer: str = ""
        for chat in self.chat_histories:
            buffer += f"Human: {chat['human']}\nAI: {chat['ai']}\n\n"

        return buffer.strip()

    def load_memory_variables(self) -> dict[str, Any]:
        """加载记忆变量为字典，便于格式化到字符串"""
        buffer_string = self.get_buffer_string()
        return {
            "chat_history": f"摘要:{self.summary}\n\n历史信息:{buffer_string}\n",
        }

    def summary_text(self, origin_summary: str, new_line: str) -> str:
        """将旧摘要和传入的新对话生成一个新摘要"""
        prompt = f"""你是一个强大的聊天机器人，请根据用户提供的谈话内容，总结内容，并将其添加到先前提供的摘要中，返回一个新的摘要, 除了新摘要，其他任何数据都不要返回

不要将<example>标签里的数据当成实际数据，这只是一个示例数据，告诉你如何生成新摘要

<example>
当前摘要: 人类会问人工智能对人工智能的看法。人工智能认为人工智能是一股向善的力量。

新的谈话内容：
Human: 为什么你认为人工智能是一股向善的力量？
AI: 因为人工智能将帮助人类充分发挥潜力。

新摘要: 人类会问人工智能对人工智能的看法。人工智能认为人工智能是一股向善的力量，因为它将帮助人类充分发挥潜力。
</example>

=============以下为实际需要处理的数据=============

当前摘要: {origin_summary}

新的对话内容:
{new_line}

新摘要:"""
        response = self._client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        return response.choices[0].message.content


client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_BASE"),
)
memory = ConversationSummaryBufferMemory("", [], 300)

# 创建一个死循环用于人机对话
while True:
    # 获取用户输入
    query = input("Human: ")

    # 判断输入是否为q, 如果是则退出
    if query == "q":
        break

    # 调用openai的chat接口
    memory_variable = memory.load_memory_variables()  # 加载记忆变量
    answer_prompt = (
        "你是一个聊天机器人，请根据用户输入回复信息\n\n"
        f"{memory_variable.get('chat_history')}\n\n"
        f"用户的提问是：{query}\n\n"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": answer_prompt},
        ],
        stream=True,
    )

    # 获取返回的内容
    print("AI: ", flush=True, end="")
    ai_content = ""
    for message in response:
        content = message.choices[0].delta.content
        if content is None:
            break
        ai_content += content
        print(content, flush=True, end="")
    print("")
    memory.save_context(query, ai_content)
