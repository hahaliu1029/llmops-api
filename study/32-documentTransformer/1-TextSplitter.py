from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import CharacterTextSplitter

loader = UnstructuredMarkdownLoader(file_path="./README.md")

document = loader.load()

splitter = CharacterTextSplitter(separator="\n\n", chunk_size=500, chunk_overlap=50)

# 分割文本
chunks = splitter.split_documents(document)

# 输出分割后的文本
for chunk in chunks:
    print(f"块大小: {len(chunk.page_content)}")
    print(chunk.page_content)

print(f"总块数: {len(chunks)}")
