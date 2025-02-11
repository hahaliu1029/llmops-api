from langchain_community.document_loaders import UnstructuredWordDocumentLoader

word_loader = UnstructuredWordDocumentLoader(
    "./InManageEBD测试验证报告.docx", mode="paged"
)

document = word_loader.load()

print(document)
print(len(document))
print(document[0].metadata)
