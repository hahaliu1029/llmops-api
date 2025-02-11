from langchain_community.document_loaders import TextLoader

# Load a text file
text_loader = TextLoader(file_path="./电商产品数据.txt", encoding="utf-8")

# Load the document
document = text_loader.load()

# Print the document
print(document)
print(len(document))
print(document[0].metadata)
