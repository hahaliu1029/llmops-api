from langchain_community.document_loaders import UnstructuredFileLoader

file_loader = UnstructuredFileLoader(
    "./副本元脑服务器 G8系列 InBry Redfish用户手册 V1.0-20241126-联合管理-20241202(3).docx",
)

document = file_loader.load()

print(document)
print(len(document))
print(document[0].metadata)
