from langchain_core.prompts import PromptTemplate

prompt = (
    PromptTemplate.from_template("讲一个{subject}实用技巧")
    + "，demo"
    + "\n使用{language}编写"
)

print(prompt)
