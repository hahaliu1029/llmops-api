from langchain_community.document_loaders import UnstructuredMarkdownLoader

loader = UnstructuredMarkdownLoader(file_path="./README.md")
document = loader.load()

print(document)
print(len(document))
print(document[0].metadata)
print(document[0].page_content)
