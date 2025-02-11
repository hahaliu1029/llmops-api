from langchain_community.document_loaders import UnstructuredPowerPointLoader

ppt_loader = UnstructuredPowerPointLoader(
    "./技术可行性-田琳-段谊海-王勇旭 -贾伟-刘一烜.pptx",
    mode="elements",
)

document = ppt_loader.load()

print(document)
print(len(document))
print(document[0].metadata)
