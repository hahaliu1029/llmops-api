from uuid import UUID
from injector import inject
from dataclasses import dataclass
from internal.schema.dataset_schema import (
    CreateDatasetReq,
    GetDatasetResp,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
    GetDatasetsWithPageResp,
)
from flask import request
from pkg.response import validate_error_json, success_message, success_json
from internal.service import DatasetService, EmbeddingsService, JiebaService
from pkg.paginator import PageModel
from internal.core.file_extractor import FileExtractor
from pkg.sqlalchemy import SQLAlchemy
from internal.model import UploadFile


@inject
@dataclass
class DatasetHandler:
    """知识库处理器"""

    dataset_service: DatasetService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    file_extractor: FileExtractor
    db: SQLAlchemy

    def embeddings_query(self):
        """文本嵌入查询"""
        upload_file = self.db.session.query(UploadFile).get(
            "535c4317-8445-47af-964e-af1abeecbd7d"
        )
        content = self.file_extractor.load(upload_file, return_text=True)
        return success_json(
            {
                "content": content,
            }
        )
        # query = request.args.get("query")
        # keywords = self.jieba_service.extract_keywords(query)
        # return success_json(
        #     {
        #         "query": query,
        #         "keywords": keywords,
        #     }
        # )
        # vectors = self.embeddings_service.embeddings.embed_query(query)
        # return success_json(
        #     {
        #         "query": query,
        #         "vectors": vectors,
        #     }
        # )

    def create_dataset(self):
        """创建知识库"""
        # 提取请求并校验
        dataset_req = CreateDatasetReq()
        if not dataset_req.validate():
            return validate_error_json(dataset_req.errors)

        # 调用服务创建知识库
        self.dataset_service.create_dataset(dataset_req)

        # 返回创建成功的知识库信息
        return success_message("创建知识库成功")

    def update_dataset(self, dataset_id: UUID):
        """根据传递的知识库id+信息更新知识库"""
        # 提取请求并校验
        dataset_req = UpdateDatasetReq()
        if not dataset_req.validate():
            return validate_error_json(dataset_req.errors)

        # 调用服务创建知识库
        self.dataset_service.update_dataset(dataset_id, dataset_req)

        # 返回创建成功的知识库信息
        return success_message("更新知识库成功")

    def delete_dataset(self):
        """删除知识库"""
        pass

    def get_dataset(self, dataset_id: UUID):
        """根据传递的知识库ID获取知识库"""
        dataset = self.dataset_service.get_dataset(dataset_id)
        res = GetDatasetResp()

        return success_json(res.dump(dataset))

    def get_datasets_with_page(self):
        """获取知识库分页+搜索列表数据"""
        # 提取请求并校验
        datasets_req = GetDatasetsWithPageReq(request.args)
        if not datasets_req.validate():
            return validate_error_json(datasets_req.errors)

        # 调用服务获取知识库分页+搜索列表数据
        datasets, paginator = self.dataset_service.get_datasets_with_page(datasets_req)

        # 构建响应
        res = GetDatasetsWithPageResp(many=True)

        return success_json(
            PageModel(
                list=res.dump(datasets),
                paginator=paginator,
            )
        )
