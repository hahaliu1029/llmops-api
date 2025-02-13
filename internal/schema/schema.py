from wtforms import Field


class ListField(Field):
    """自定义List字段，用于存储列表类型数据"""

    data: list = None

    def process_formdata(self, valuelist):
        """处理表单数据"""
        if valuelist is not None and isinstance(valuelist, list):
            self.data = valuelist

    def _value(self):
        """获取字段值"""
        print("self.data", self.data)
        return self.data if self.data is not None else []
