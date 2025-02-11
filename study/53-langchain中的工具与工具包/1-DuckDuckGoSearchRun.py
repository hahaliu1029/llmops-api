from langchain_community.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun()

print("工具名字: ", search.name)
print("工具描述: ", search.description)
print("工具参数:", search.args)
print("是否直接返回: ", search.return_direct)
print(search.run("InManage是什么?"))
