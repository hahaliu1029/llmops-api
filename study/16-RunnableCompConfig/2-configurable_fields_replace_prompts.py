from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import ConfigurableField

prompt = PromptTemplate.from_template(
    "请生成一个小于{x}的随机整数"
).configurable_fields(
    template=ConfigurableField(
        id="prompt_template",
        name="模板",
        description="模板",
    )
)

content = prompt.invoke(
    {"x": 1000},
    config={"configurable": {"prompt_template": "请生成一个大于{x}的随机整数"}},
).to_string()

print(content)
