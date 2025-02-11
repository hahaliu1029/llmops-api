from langchain_community.document_loaders import WebBaseLoader

web_loader = WebBaseLoader(
    "https://support.ieisystem.com/eportal/ui?pageId=2317460&type=0",
)

document = web_loader.load()

print(document)
print(len(document))
print(document[0].metadata)
