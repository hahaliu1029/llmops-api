# Description: 重用PromptTemplate
from langchain_core.prompts import PromptTemplate, PipelinePromptTemplate

full_prompt = PromptTemplate.from_template(
    """{instruction}

{example}

{start}
"""
)

# 描述模版
instruction_prompt = PromptTemplate.from_template("你正在模拟{person}")

# 例子模版
example_prompt = PromptTemplate.from_template(
    """下面是一个例子：

    Q: {example_q}
    A: {example_a}"""
)

# 开始模版
start_prompt = PromptTemplate.from_template(
    """现在，你是一个真实的人，请回答用户的问题:
    
    Q: {input}
    A:"""
)

# 模版组合
pipeline_prompts = [
    ("instruction", instruction_prompt),
    ("example", example_prompt),
    ("start", start_prompt),
]

pipeline_prompt = PipelinePromptTemplate(
    final_prompt=full_prompt, pipeline_prompts=pipeline_prompts
)

print(
    pipeline_prompt.invoke(
        {
            "person": "一个真实的人",
            "example_q": "你叫什么名字？",
            "example_a": "我叫小明",
            "input": "你好，我想了解Python的实用技巧",
        }
    ).to_string()
)
