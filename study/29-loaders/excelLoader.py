from langchain_community.document_loaders import UnstructuredExcelLoader

excel_loader = UnstructuredExcelLoader("./月度绩效-前端-FY2024.xlsx")

document = excel_loader.load()

print(document)
print(len(document))
print(document[0].metadata)
