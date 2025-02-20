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


class DictField(Field):
    """自定义Dict字段，用于存储字典类型数据"""

    data: dict = None

    def process_formdata(self, valuelist):
        """处理表单数据"""
        if (
            valuelist is not None
            and len(valuelist) > 0
            and isinstance(valuelist[0], dict)
        ):
            self.data = valuelist[0]

    def _value(self):
        """获取字段值"""
        return self.data
