import os
from pathlib import Path
import tempfile
from typing import Union
from injector import inject
from dataclasses import dataclass

import requests
from internal.service import CosService
from internal.model import UploadFile
from langchain_core.documents import Document as LCDocument
from langchain_community.document_loaders import (
    UnstructuredExcelLoader,
    UnstructuredPDFLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    UnstructuredCSVLoader,
    UnstructuredPowerPointLoader,
    UnstructuredXMLLoader,
    UnstructuredFileLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
)


@inject
@dataclass
class FileExtractor:
    """文件提取器, 用于将远程文件、upload_file记录加载成LangChain对应的文档或字符串"""

    cos_service: CosService

    def load(
        self,
        upload_file: UploadFile,
        return_text: bool = False,
        is_unstructured: bool = True,
    ) -> Union[list[LCDocument], str]:
        """加载传入的upload_file记录，返回LangChain文档列表或字符串"""
        # 创建一个临时的文件夹
        with tempfile.TemporaryDirectory() as temp_dir:
            # 构建一个临时文件路径
            file_path = os.path.join(temp_dir, os.path.basename(upload_file.key))

            # 将对象存储中的文件下载到本地
            self.cos_service.download_file(upload_file.key, file_path)

            # 从指定的路径中去加载文件
            return self.load_from_file(file_path, return_text, is_unstructured)

    @classmethod
    def load_from_url(
        cls, url: str, return_text: bool = False
    ) -> Union[list[LCDocument], str]:
        """加载指定的URL，返回LangChain文档列表或字符串"""
        # 下载文件到本地
        response = requests.get(url)

        # 创建一个临时的文件夹
        with tempfile.TemporaryDirectory() as temp_dir:
            # 构建一个临时文件路径
            file_path = os.path.join(temp_dir, os.path.basename(url))

            with open(file_path, "wb") as file:
                file.write(response.content)

            return cls.load_from_file(file_path, return_text)

    @classmethod
    def load_from_file(
        cls, file_path: str, return_text: bool = False, is_unstructured: bool = True
    ) -> Union[list[LCDocument], str]:
        """加载指定路径的文件，返回LangChain文档列表或字符串"""
        # 获取文件的扩展名
        delimiter = "\n\n"
        file_extension = Path(file_path).suffix.lower()

        # 根据不同的文件扩展名加载不同加载器
        if file_extension in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(file_path)
        elif file_extension == ".pdf":
            loader = UnstructuredPDFLoader(file_path)
        elif file_extension in [".md", ".markdown"]:
            loader = UnstructuredMarkdownLoader(file_path)
        elif file_extension in [".html", ".htm"]:
            loader = UnstructuredHTMLLoader(file_path)
        elif file_extension == ".csv":
            loader = UnstructuredCSVLoader(file_path)
        elif file_extension in [".ppt", ".pptx"]:
            loader = UnstructuredPowerPointLoader(file_path)
        elif file_extension == ".xml":
            loader = UnstructuredXMLLoader(file_path)
        elif file_extension in [".doc", ".docx"]:
            loader = UnstructuredWordDocumentLoader(file_path, mode="paged")
        else:
            loader = (
                UnstructuredFileLoader(file_path)
                if is_unstructured
                else TextLoader(file_path)
            )

        # 返回加载的文档列表或者文本
        return (
            delimiter.join([doc.page_content for doc in loader.load()])
            if return_text
            else loader.load()
        )
