from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = UnstructuredMarkdownLoader(file_path="./项目API文档.md")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50, add_start_index=True
)

chunks = splitter.split_documents(documents)

for chunk in chunks:
    print(f"块大小: {len(chunk.page_content)}, 元数据: {chunk.metadata}")
