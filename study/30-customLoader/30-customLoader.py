from typing import AsyncIterator, Iterator
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class CustomDocumentLoader(BaseLoader):
    """自定义文档加载器， 将文本文件的每一行都解析为Document"""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def lazy_load(self) -> Iterator[Document]:
        # 读取对应文件
        with open(self.file_path, encoding="utf-8") as f:
            line_number = 0
            for line in f:
                yield Document(
                    page_content=line,
                    metadata={"score": self.file_path, "line_number": line_number},
                )
                line_number += 1

    async def alazy_load(self) -> AsyncIterator[Document]:
        import aiofiles

        async with aiofiles.open(self.file_path, encoding="utf-8") as f:
            line_number = 0
            async for line in f:
                yield Document(
                    page_content=line,
                    metadata={"score": self.file_path, "line_number": line_number},
                )
                line_number += 1


loader = CustomDocumentLoader("./喵喵.txt")

document = loader.load()

print(document)
print(len(document))
print(document[0].metadata)
