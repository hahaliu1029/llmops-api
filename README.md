# 本项目API文档

应用 API 接口统一以 JSON 格式返回，并且包含 3 个字段：`code`、`message`、`data`, 分别代表`业务状态码`、`提示信息`、`业务数据`。

`业务状态码`共6种，其中只有 `success(成功)` 代表业务成功，其余均代表业务失败，并且失败会附加相关的信息：`fail(通用失败)`、`not_found(未找到)`、`unauthorized(未授权)`、`forbidden(无权限)`和`validate_error(数据验证失败)`。

接口示例：

```json
{
    "code": "success",
    "data": {
        "redirect_url": "https://github.com/login/oauth/authorize?client_id=f69102c6b97d90d69768&redirect_uri=http%3A%2F%2Flocalhost%3A5001%2Foauth%2Fauthorize%2Fgithub&scope=user%3Aemail"
    },
    "message": ""
}

```

带有分页数据的接口会在 `data` 内固定传递 `list` 和 `paginator` 字段，其中 `list` 代表分页后的列表数据，`paginator` 代表分页的数据。

`paginator` 内存在 4 个字段：`current_page(当前页数)` 、`page_size(每页数据条数)`、`total_page(总页数)`、`total_record(总记录条数)`，示例数据如下：

```json
{
    "code": "success",
    "data": {
        "list": [
            {
                "app_count": 0,
                "created_at": 1713105994,
                "description": "这是专门用来存LLMOps的知识库",
                "document_count": 13,
                "icon": "https://a.com/111.png",
                "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
                "name": "LLMOps知识库",
                "updated_at": 1713106758,
                "word_count": 8850
            }
        ],
        "paginator": {
            "current_page": 1,
            "page_size": 20,
            "total_page": 1,
            "total_record": 2
        }
    },
    "message": ""
}
```

如果接口需要授权，需要在 `headers` 中添加 `Authorization` ，并附加 `access_token` 即可完成授权登录，示例：

```shell
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTY0NTY3OTgsImlzcyI6ImxsbW9wcyIsInN1YiI6ImM5MDljMWRiLWIyMmUtNGZlNi04OGIyLWIyZTkxZWFiMWE3YiJ9.JDAtWDBBGiXa_XFihfopRe4Cz-RQ9_TAcno9w81tNbE
```

## 1. 应用模块

### 1.1 [todo]获取应用基础信息

- **接口说明**：传递对应的应用 id，获取当前应用的基础信息+配置信息等内容。

- **接口信息**: `授权` + `GET:/apps/:app_id`

- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| app_id | uuid | 是 | 需要获取的应用 id |

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 | | |
| --- | --- | --- | --- | ---|
| id | uuid | 应用 id | | |
| name | string | 应用名称 | | |
| icon | string | 应用图标 | | |
| description | string | 应用描述 | | |
| published_app_config_id | uuid | 已发布应用配置 id，如果不存在则为 null | | |
| drafted_app_config_id | uuid | 草稿应用配置 id，如果不存在则为 null | | |
| debug_conversation_id | uuid | 调试会话 id，如果不存在则为 null | | |
| published_app_config/drafted_app_config | json | 应用配置信息,涵盖草稿配置、已发布配置，如果没有则为 null，两个配置的变量信息一致 | | |
| | 字段名称 | 字段类型 | 字段说明 | |
| | id | uuid | 配置 id | |
| | model_config | json | 模型配置 | |
| | | dialog_round | int | 携带上下文轮数，类型为非负整型 |
| | memory_mode | string | 记忆模式，涵盖 `long_term_memory(长记忆)` 和 `none(无记忆)` 两种 |
| | status | string | 应用配置配置状态，涵盖 `drafted(草稿)` 和 `published(已发布)` 两种 |
| | created_at | int | 应用配置创建时间 | |
| | updated_at | int | 应用配置更新时间 | |
| updated_at | int | 更新时间 | | |
| created_at | int | 创建时间 | | |
||||||

- **响应示例**：

```json
{
    "code": "success",
    "data": {
        "icon": "https://a.com/111.png",
        "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "name": "LLMOps知识库",
        "description": "这是专门用来存LLMOps的知识库",
        "published_app_config_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "drafted_app_config_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "debug_conversation_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "published_app_config": {
            "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
            "model_config": {
                "dialog_round": 3
            },
            "memory_mode": "long_term_memory",
            "status": "published",
            "created_at": 1713105994,
            "updated_at": 1713106758
        },
        "drafted_app_config": {
            "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
            "model_config": {
                "dialog_round": 3
            },
            "memory_mode": "long_term_memory",
            "status": "drafted",
            "created_at": 1713105994,
            "updated_at": 1713106758
        },
        "updated_at": 1713106758,
        "created_at": 1713105994
    },
    "message": ""
}
```

### 1.2 [todo]更新应用草稿配置信息

- **接口说明**：更新应用的草稿配置信息，涵盖：模型配置、长记忆模式等，该接口会查找该应用原始的草稿配置并进行更新，如果没有原始草稿配置，则创建一个新配置作为草稿配置。

- **接口信息**: `授权` + `PUT:/apps/:app_id/config`

- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| app_id | uuid | 是 | 需要更新的应用 id |
| model_config | json | 是 | 模型配置信息 |
| | 字段名称 | 字段类型 | 字段说明 |
| | dialog_round | int | 携带上下文轮数，类型为非负整型 |
| memory_mode | string | 是 | 记忆模式，涵盖 `long_term_memory(长记忆)` 和 `none(无记忆)` 两种 |

- **请求示例**：

```json
{
    "model_config": {
        "dialog_round": 3
    },
    "memory_mode": "long_term_memory"
}
```

- **响应示例**:

```json
{
    "code": "success",
    "data": {},
    "message": "更新AI应用配置成功"
}
```

### 1.3 [todo]获取应用调试长记忆

- **接口说明**：获取应用的调试长记忆，该接口会返回当前应用的长记忆信息, 如果该应用并没有开启长记忆，则会抛出错误信息。

- **接口信息**: `授权` + `GET:/api/apps/:app_id/long-term-memory`

- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| app_id | uuid | 是 | 需要获取的应用 id |

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 | | |
| --- | --- | --- | --- | ---|
| id | uuid | 应用 id | | |
| name | string | 应用名称 | | |
| icon | string | 应用图标 | | |
| description | string | 应用描述 | | |
| published_app_config_id | uuid | 已发布应用配置 id，如果不存在则为 null | | |
| drafted_app_config_id | uuid | 草稿应用配置 id，如果不存在则为 null | | |
| debug_conversation_id | uuid | 调试会话 id，如果不存在则为 null | | |
| published_app_config/drafted_app_config | json | 应用配置信息,涵盖草稿配置、已发布配置，如果没有则为 null，两个配置的变量信息一致 | | |
| | 字段名称 | 字段类型 | 字段说明 | |
| | id | uuid | 配置 id | |
| | model_config | json | 模型配置 | |
| | | dialog_round | int | 携带上下文轮数，类型为非负整型 |
| | memory_mode | string | 记忆模式，涵盖 `long_term_memory(长记忆)` 和 `none(无记忆)` 两种 |
| | status | string | 应用配置配置状态，涵盖 `drafted(草稿)` 和 `published(已发布)` 两种 |
| | created_at | int | 应用配置创建时间 | |
| | updated_at | int | 应用配置更新时间 | |
| updated_at | int | 更新时间 | | |
| created_at | int | 创建时间 | | |
||||||

- **响应示例**：

```json
{
    "code": "success",
    "data": {
        "icon": "https://a.com/111.png",
        "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "name": "LLMOps知识库",
        "description": "这是专门用来存LLMOps的知识库",
        "published_app_config_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "drafted_app_config_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "debug_conversation_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "published_app_config": {
            "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
            "model_config": {
                "dialog_round": 3
            },
            "memory_mode": "long_term_memory",
            "status": "published",
            "created_at": 1713105994,
            "updated_at": 1713106758
        },
        "drafted_app_config": {
            "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
            "model_config": {
                "dialog_round": 3
            },
            "memory_mode": "long_term_memory",
            "status": "drafted",
            "created_at": 1713105994,
            "updated_at": 1713106758
        },
        "updated_at": 1713106758,
        "created_at": 1713105994
    },
    "message": ""
}
```

### 1.4 [todo]更新应用调试长记忆

- **接口说明**：更新应用的调试长记忆，该接口会更新当前应用的长记忆信息, 如果该应用并没有开启长记忆，则会抛出错误信息。

- **接口信息**: `授权` + `POST:/apps/:app_id/long-term-memory`

- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| app_id | uuid | 是 | 需要更新的应用 id (路由参数) |
| summary | string | 是 | 长记忆的总结信息 |

- **请求示例**：

```json
{
    "summary": "这是一个长记忆的总结信息"
}
```

- **响应示例**:

```json
{
    "code": "success",
    "data": {},
    "message": "更新AI应用长记忆成功"
}
```

### 1.5 [todo]应用调试对话

- **接口说明**：用于在编排 AI 应用时进行 debug 调试，如果当前应用没有草稿配置，则使用发布配置进行调试，如果有草稿配置则以草稿配置信息进行调试。

- **接口信息**: `授权` + `POST:/apps/:app_id/debug`

- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| app_id | uuid | 是 | 需要调试的应用 id |
| query | string | 是 | 用户输入的 query 信息 |

- **请求示例**：

```json
{
    "query": "你好"
}
```

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 | 
| --- | --- | --- |
| id | uuid | 响应消息的 id |
| conversation_id | uuid | 消息关联会话的 id |
| query | string | 用户输入的 query 信息 |
| answer | string | AI 应用返回的回答信息 |
| answer_tokens | int | 生成消耗的token数 |
| response_latency | float | 响应延迟时间, 单位为毫秒 |
| created_at | int | 消息创建时间 |
| updated_at | int | 消息更新时间 |

- **响应示例**:

```json
{
    "code": "success",
    "data": {
        "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "conversation_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
        "query": "你好",
        "answer": "你好，我是AI助手",
        "answer_tokens": 3,
        "response_latency": 0.1,
        "created_at": 1713105994,
        "updated_at": 1713106758
    },
    "message": ""
}
```

### 1.6 [todo]获取应用调试历史对话列表

- **接口说明**：用于获取应用调试历史对话列表信息，该接口支持分页，单次最多返回 20 组对话消息，并且分页以时间字段进行降序，接口不会返回软删除对应的数据。

- **接口信息**: `授权` + `GET:/apps/:app_id/messages`

- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| app_id | uuid | 是 | 需要获取的应用 id |

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 |
| --- | --- | --- |
| id | uuid | 响应消息的 id |
| conversation_id | uuid | 消息关联会话的 id |
| query | string | 用户输入的 query 信息 |
| answer | string | AI 应用返回的回答信息 |
| answer_tokens | int | 生成消耗的token数 |
| response_latency | float | 响应延迟时间, 单位为毫秒 |
| created_at | int | 消息创建时间 |
| updated_at | int | 消息更新时间 |

- **响应示例**:

```json
{
    "code": "success",
    "data": {
        "list": [
            {
                "id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
                "conversation_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
                "query": "你好",
                "answer": "你好，我是AI助手",
                "answer_tokens": 3,
                "response_latency": 0.1,
                "created_at": 1713105994,
                "updated_at": 1713106758
            }
        ],
        "paginator": {
            "current_page": 1,
            "page_size": 20,
            "total_page": 1,
            "total_record": 2
        }
    },
    "message": ""
}
```

### 1.7 [todo]删除特定的调试消息

- **接口说明**：用于删除 AI 应用调试对话过程中指定的消息，该删除会在后端执行软删除操作，并且只有当会话 id 和消息 id 都匹配上时，才会删除对应的调试消息。

- **接口信息**: `授权` + `POST:/apps/:app_id/messages/:message_id/delete`

- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| app_id | uuid | 是 | 需要删除的应用 id |
| message_id | uuid | 是 | 需要删除的消息 id |

- **请求示例**：

```json
{
    "app_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401",
    "message_id": "c0759ca8-2d35-4480-83a8-1f41f29d1401"
}
```

- **响应示例**:

```json
{
    "code": "success",
    "data": {},
    "message": "删除AI应用调试消息成功"
}
```

## 插件模块

### 2.1 获取内置插件分类表

- **接口说明**：用于获取插件广场页面中所有插件的分类信息，该接口不支持分页，会一次性返回所有信息。
- **接口信息**: `授权` + `GET:/builtin-tools/categories`
- **请求参数**：无
- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 |
| --- | --- | --- |
| icon | string | 分类图标 |
| category | string | 分类英文唯一标识名，例如 search、image、weather 等，用于在前端进行唯一标识判断 |
| name | string | 分类名称 |

- **响应示例**：

```json
{
    "code": "success",
    "data": [
        {"category": "search", "name": "搜索", "icon": "xxx"},
        {"category": "image", "name": "图片", "icon": "xxx"},
        {"category": "videos", "name": "视频", "icon": "xxx"}
    ],
    "message": ""
}
```

### 2.2 获取所有内置插件列表信息

- **接口说明**：获取 LLMOps 项目中所有内置插件列表信息，该接口会一次性获取所有提供商/工具，无分页，适用于 插件广场 与 AI应用编排 页面。
- **接口信息**: `授权` + `GET:/builtin-tools`
- **请求参数**：无
- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 | | | |
| --- | --- | --- | --- | ---|---|
| name | string | 提供商的名称。 | | | |
| label | string | 提供商对应的标签。 | | | |
| category | string | 提供商对应的分类。 | | | |
| background | string | 提供商 icon 图标的背景。 | | | |
| tools | list | 提供商下的工具列表。 | | | |
| | name | string | 工具名称。 | | |
| | label | string | 工具对应的标签。 | | |
| | inputs | list | 大语言模型调用对应的参数，如果没有则为空列表，该参数信息对应 LLM 工具调用的信息完全一致，不做任何转换。 | | |
| | | name | string | 参数名称。 | |
| | | description | string | 参数描述。 | |
| | | required | bool | 是否必填。 | |
| | | type | string | 参数类型。 | |
| | params | list | 工具设置对应的参数列表信息，如果没有则为空。 | | |
| | | name | string | 参数名称。 | |
| | | label | string | 参数对应的标签。 | |
| | | type | string | 参数类型,涵盖了 string、number、boolean、select。 | |
| | | default | Any | 参数默认值。如果没有默认值则为 None。 | |
| | | required | bool | 是否必填。 | |
| | | min | float | 参数最小值。如果不需要则为 None | |
| | | max | float | 参数最大值。如果不需要则为 None | |
| | | help | string | 参数帮助信息, 如果没有则为 None 或者空字符串。 | |
| | | options | list | 类型为下拉列表时需要配置的选项。 | |
| | | | label | string | 选项名称。 |
| | | | value | string | 下拉菜单对应的值 |
| created_at | int | 创建/发布该服务商插件的时间戳。| | ||

- **响应示例**：

```json

{
    "code": "success",
    "data": [
        {
            "name": "google",
            "label": "Google",
            "description": "谷歌服务提供商，涵盖了谷歌搜索等工具。",
            "background": "#E5E7EB",
            "category": "search",
            "tools": [
                {
                    "name": "google_serper",
                    "label": "谷歌Serper搜索",
                    "description": "一个低成本的谷歌搜索API。",
                    "inputs": [
                        {
                            "name": "query",
                            "description": "输入应该是搜索查询语句",
                            "required": true,
                            "type": "string"
                        }
                    ],
                    "params": [],
                }
            ],
            "created_at": 1721460914
        },
        {
            "name": "dalle",
            "label": "DALLE",
            "description": "DALLE是一个文生图工具。",
            "background": "#E5E7EB",
            "category": "image",
            "tools": [
                {
                    "name": "dalle3",
                    "label": "DALLE-3绘图工具",
                    "description": "DALLE-3是一个将文本转换成图片的绘图工具",
                    "inputs": [
                        {
                            "name": "query",
                            "description": "输入应该是生成图像的文本提示(prompt)",
                            "required": true,
                            "type": "string"
                        }
                    ],
                    "params": [
                        {
                            "name": "size",
                            "label": "图片尺寸",
                            "type": "select",
                            "required": true,
                            "help": "",
                            "min": null,
                            "max": null,
                            "options": [
                                {"value": "1024×1024", "label": "(方)1024x1024"},
                                {"value": "1792x1024", "label": "(横屏)1792x1024"},
                                {"value": "1024x1792", "label": "(竖屏)1024x1792"}
                            ]
                        },
                        {
                            "name": "style",
                            "label": "图片风格",
                            "type": "select",
                            "required": true,
                            "help": "",
                            "min": null,
                            "max": null,
                            "options": [
                                {"value": "vivid", "label": "生动"},
                                {"value": "natural", "label": "自然"}
                            ]
                        }
                    ]
                }
            ],
            "created_at": 1721460914
        }
    ],
    "message": ""
}

```

### 2.3 获取指定工具的信息

- **接口说明**：根据传递的 提供商名称 + 工具名称 获取对应工具信息详情，该接口用于在 AI 应用编排页面，点击工具设置时进行相应的展示
- **接口信息**: `授权` + `GET:/builtin-tools/:provider/tools/:tool`
- **请求参数**：
  
| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| provider | string | 是 | 路由参数，服务提供商对应的名字，例如 google、dalle 等。|
| tool | string | 是 | 路由参数，工具对应的名字，例如 google_serper、dalle3 等。|

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 | | | |
| --- | --- | --- | --- | ---|---|
| provider | dict | 该工具所属的提供商对应的信息字典。 | | | |
| | name | string | 提供商的名称。 | | |
| | label | string | 提供商对应的标签。 | | |
| | category | string | 提供商对应的分类。 | | |
| | background | string | 提供商 icon 图标的背景。 | | |
| | description | string | 提供商的描述信息。 | | |
| name | string | 工具名称。 | | | |
| label | string | 工具对应的标签。 | | | |
| description | string | 工具的描述信息。 | | | |
| inputs | list | 大语言模型调用对应的参数，如果没有则为空列表，该参数信息对应 LLM 工具调用的信息完全一致，不做任何转换。 | | | |
| | name | string | 参数名称。 | | |
| | description | string | 参数描述。 | | |
| | required | bool | 是否必填。 | | |
| | type | string | 参数类型。 | | |
| params | list | 工具设置对应的参数列表信息，如果没有则为空。 | | | |
| | name | string | 参数名称。 | | |
| | label | string | 参数对应的标签。 | | |
| | type | string | 参数类型,涵盖了 string、number、boolean、select。 | | |
| | default | Any | 参数默认值。如果没有默认值则为 None。 | | |
| | required | bool | 是否必填。 | | |
| | min | float | 参数最小值。如果不需要则为 None | | |
| | max | float | 参数最大值。如果不需要则为 None | | |
| | help | string | 参数帮助信息, 如果没有则为 None 或者空字符串。 | | |
| | options | list | 类型为下拉列表时需要配置的选项。 | | |
| | | label | string | 选项名称。 | |
| | | value | string | 下拉菜单对应的值 | |
| created_at | int | 创建工具的创建时间。| | | |

- **请求示例**：

```shell
GET: /buildin-tools/google/tools/google_serper
```

- **响应示例**：

```json
{
    "code": "success",
    "data": {
        "provider": {
            "name": "dalle",
            "label": "DALLE",
            "description": "DALLE是一个文生图工具。",
            "background": "#E5E7EB",
            "category": "image"
        },
        "name": "dalle3",
        "label": "DALLE-3绘图工具",
        "description": "DALLE-3是一个将文本转换成图片的绘图工具",
        "inputs": [
            {
                "name": "query",
                "description": "输入应该是生成图像的文本提示(prompt)",
                "required": true,
                "type": "string"
            }
        ],
        "params": [
            {
                "name": "size",
                "label": "图片尺寸",
                "type": "select",
                "required": true,
                "help": "",
                "min": null,
                "max": null,
                "options": [
                    {"value": "1024×1024", "label": "(方)1024x1024"},
                    {"value": "1792x1024", "label": "(横屏)1792x1024"},
                    {"value": "1024x1792", "label": "(竖屏)1024x1792"}
                ]
            },
            {
                "name": "style",
                "label": "图片风格",
                "type": "select",
                "required": true,
                "help": "",
                "min": null,
                "max": null,
                "options": [
                    {"value": "vivid", "label": "生动"},
                    {"value": "natural", "label": "自然"}
                ]
            }
        ],
        "created_at": 15121213465,
    },
    "message": ""
}
```

### 2.4 获取内置插件提供商icon

- **接口说明**：根据传递的 服务提供商名称 对应的 icon 信息，返回的是 icon 图片流，例如 svg 图片就是对应的源码，png/jpeg 等就是图片流信息。
- **接口信息**: `授权` + `GET:/builtin-tools/:provider/icon`
- **请求参数**：
  
| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| provider | string | 是 | 路由参数，服务提供商对应的名字，例如 google、dalle 等。|

- **请求示例**：

```shell
GET: /buildin-tools/google/icon
```

- **响应示例**：

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="25" viewBox="0 0 24 25" fill="none">
  <path d="M22.501 12.7332C22.501 11.8699 22.4296 11.2399 22.2748 10.5865H12.2153V14.4832H18.12C18.001 15.4515 17.3582 16.9099 15.9296 17.8898L15.9096 18.0203L19.0902 20.435L19.3106 20.4565C21.3343 18.6249 22.501 15.9298 22.501 12.7332Z" fill="#4285F4"/>
  <path d="M12.214 23C15.1068 23 17.5353 22.0666 19.3092 20.4567L15.9282 17.8899C15.0235 18.5083 13.8092 18.9399 12.214 18.9399C9.38069 18.9399 6.97596 17.1083 6.11874 14.5766L5.99309 14.5871L2.68583 17.0954L2.64258 17.2132C4.40446 20.6433 8.0235 23 12.214 23Z" fill="#34A853"/>
  <path d="M6.12046 14.5766C5.89428 13.9233 5.76337 13.2233 5.76337 12.5C5.76337 11.7766 5.89428 11.0766 6.10856 10.4233L6.10257 10.2841L2.75386 7.7355L2.64429 7.78658C1.91814 9.20993 1.50146 10.8083 1.50146 12.5C1.50146 14.1916 1.91814 15.7899 2.64429 17.2132L6.12046 14.5766Z" fill="#FBBC05"/>
  <path d="M12.2141 6.05997C14.2259 6.05997 15.583 6.91163 16.3569 7.62335L19.3807 4.73C17.5236 3.03834 15.1069 2 12.2141 2C8.02353 2 4.40447 4.35665 2.64258 7.78662L6.10686 10.4233C6.97598 7.89166 9.38073 6.05997 12.2141 6.05997Z" fill="#EB4335"/>
</svg>
```

### 2.5 获取自定义 API 工具提供者列表

- **接口说明**：获取特定账号创建的 API 插件/自定义工具信息，该接口携带分页，并支持搜索
- **接口信息**: `授权` + `GET:/api-tools`
- **请求参数**：
  
| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| search_word | string | 否 | 搜索词，用于搜索自定义 API 工具，默认为空代表不搜索任何内容 |
| current_page | int | 否 | 当前页码，默认为 1 |
| page_size | int | 否 | 每页返回的数据量，默认为 20，范围从 1~50 |

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 | | | |
| --- | --- | --- | --- | ---| ---|
| list | list | 分页后的 API 插件列表，列表里的每一个元素都是一个字典。 | | | |
| | id | uuid | 当前工具提供者对应的 id。 | ||
| | name | string | 工具提供者的名称。 | ||
| | icon | string | 工具提供者的 icon 图标。 | ||
| | tools | list | 该工具提供商的所有工具列表信息。 | ||
| | | id | uuid | 工具的 id。 ||
| | | description | string | 工具的描述信息。 ||
| | | name | string | 工具的名称,同一个提供者下的工具名称不能重复。 ||
| | | inputs | list | 工具的大语言模型输入列表，列表里的每一个元素都是一个字典。 ||
| | | | name | string | 参数名称。 |
| | | | description | string | 参数描述。 |
| | | | required | bool | 是否必填。 |
| | | | type | string | 参数类型。 |
| | description | string | 工具提供者的描述信息。 | | |
| | headers | list | 工具提供者的请求头信息。 | | |
| | | key | string | 请求头的 key。 | |
| | | value | string | 请求头的 value。 | |
| | created_at | int | 工具提供者的创建时间。 | | |
| paginator | dict | 分页信息字典。 | | | |
| | current_page | int | 当前页码。 | | |
| | page_size | int | 每页返回的数据量。 | | |
| | total_page | int | 总页数。 | | |
| | total_record | int | 总记录数。 | | |

- **请求示例**：

```shell
/api-tools?search_word=&current_page=1&page_size=21
```

- **响应示例**：

```json
{
    "code": "success",
    "data": {
        "list": [
            {
                "id": "46db30d1-3199-4e79-a0cd-abf12fa6858f",
                "name": "高德工具包",
                "icon": "https://cdn.imooc.com/gaode.png",
                "description": "查询ip所在地、天气预报、路线规划等高德工具包",
                "tools": [
                    {
                        "id": "d400cec0-892f-49ab-8f72-821b88c1aaa9",
                        "description": "根据传递的城市名获取指定城市的天气预报，例如：广州。",
                        "name": "GetCurrentWeather",
                        "inputs": [
                            {
                                "type": "str",
                                "required": true,
                                "name": "query",
                                "description": "需要搜索的查询语句"
                            }
                        ]
                    }
                ],
                "headers": [
                    {"key": "Authorization", "value": "Bearer QQYnRFerJTSEcrfB89fw8prOaObmrch8"}
                ],
                "created_at": 1721460914
            }
        ],
        "paginator": {
            "current_page": 1,
            "page_size": 21,
            "total_page": 1,
            "total_record": 2
        }
    },
    "message": ""
}
```

### 2.6 创建自定义 API 工具提供者

- **接口说明**：用于将企业现有的 API 服务接入到 LLMOps 项目创建自定义 API 工具，对于该自定义工具，支持 GET+POST 两种 HTTP 方法的 URL 链接，并且对 OpenAPI-Schema 规范进行简化+调整，以让其更适配 LLMOps 项目
- **接口信息**: `授权` + `POST:/api-tools`
- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 ||
| --- | --- | --- | --- | ---|
| name | string | 是 | 工具提供者的名称,同一个账号下的工具提供商名字必须唯一，否则容易识别错误，名字的长度范围是 0-30 个字符 ||
| icon | string | 是 | 工具提供者的 icon 图标，用于在工具列表中进行展示，icon,类型为图片 URL 字符串 ||
| openapi_schema | str | 是 | OpenAPI-Schema 规范的 JSON 字符串,在字符串中涵盖基础信息、服务，该数据在后端会进行校验，如果缺少了对应的数据会抛出数据校验错误 ||
| headers | list | 是 | 接口附加的请求头信息，类型为列表，列表的每个元素都是一个字典，如果没有请求头信息则传递空列表即可。 ||
| | key | string | 请求头的 key。 | |
| | value | string | 请求头的 value。 | |

- **请求示例**：

```json
{
    "name": "谷歌搜索",
    "icon": "https://cdn.imooc.com/google.png",
    "openapi_schema": "{\"description\":\"这是一个查询对应英文单词字典的工具\",\"server\":\"https://dict.youdao.com\",\"paths\":{\"/suggest\":{\"get\":{\"description\":\"根据传递的单词查询其字典信息\",\"operationId\":\"YoudaoSuggest\",\"parameters\":[{\"name\":\"q\",\"in\":\"query\",\"description\":\"要检索查询的单词，例如love/computer\",\"required\":true,\"type\":\"str\"},{\"name\":\"doctype\",\"in\":\"query\",\"description\":\"返回的数据类型，支持json和xml两种格式，默认情况下json数据\",\"required\":false,\"type\":\"str\"}]}}}}",
    "headers": [
        {
            "key": "Authorization",
            "value": "Bearer QQYnRFerJTSEcrfB89fw8prOaObmrch8"
        }
    ]
}
```

- **响应示例**：

```json
{
    "code": "success",
    "data": {},
    "message": "创建自定义 API 工具提供者成功"
}
```

### 2.7 删除自定义 API 工具提供者

- **接口说明**：用于删除特定的自定义 API 插件，删除对应的 API 插件后，关联的应用、工作流也无法使用该插件/工具（在应用对话交流、工作流运行之前都会检测对应的 API 插件是否存在，如果被删除了，均会剔除并无法使用）。
- **接口信息**: `授权` + `POST:/api-tools/:provider_id/delete
- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| provider_id | uuid | 是 | 路由参数，需要删除的 API 工具提供商 id，类型为 uuid。 |

- **请求示例**：

```shell
POST:/api-tools/e1baf52a-1be2-4b93-ad62-6fad72f1ec37/delete
```

- **响应示例**：

```json
{
    "code": "success",
    "data": {},
    "message": "删除自定义 API 工具提供者成功"
}
```

### 2.8 更新自定义 API 工具提供者

- **接口说明**：用于更新自定义 API 工具信息，每次更新的时候，在后端都会删除原有工具信息，并记录创建新的工具数据，在后端使用 provider_id+tool_name 唯一标识进行判断，更新时如果同个账号出现重名，则会抛出错误。
- **接口信息**: `授权` + `POST:/api-tools/:provider_id
- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 ||
| --- | --- | --- | --- | ---|
| provider_id | uuid | 是 | 路由参数，需要更新的 API 工具提供商 id，类型为 uuid。 ||
| name | string | 是 | 工具提供者的名称,同一个账号下的工具提供商名字必须唯一，否则容易识别错误，名字的长度范围是 0-30 个字符 ||
| icon | string | 是 | 工具提供者的 icon 图标，用于在工具列表中进行展示，icon,类型为图片 URL 字符串 ||
| openapi_schema | str | 是 | OpenAPI-Schema 规范的 JSON 字符串,在字符串中涵盖基础信息、服务，该数据在后端会进行校验，如果缺少了对应的数据会抛出数据校验错误 ||
| headers | list | 是 | 接口附加的请求头信息，类型为列表，列表的每个元素都是一个字典，如果没有请求头信息则传递空列表即可。 ||
| | key | string | 请求头的 key。 | |
| | value | string | 请求头的 value。 | |

- **请求示例**：

```json
POST:/api-tools/e1baf52a-1be2-4b93-ad62-6fad72f1ec37

{
    "name": "",
    "icon": "",
    "openapi_schema": "{\"description\":\"这是一个查询对应英文单词字典的工具\",\"server\":\"https://dict.youdao.com\",\"paths\":{\"/suggest\":{\"get\":{\"description\":\"根据传递的单词查询其字典信息\",\"operationId\":\"YoudaoSuggest\",\"parameters\":[{\"name\":\"q\",\"in\":\"query\",\"description\":\"要检索查询的单词，例如love/computer\",\"required\":true,\"type\":\"str\"},{\"name\":\"doctype\",\"in\":\"query\",\"description\":\"返回的数据类型，支持json和xml两种格式，默认情况下json数据\",\"required\":false,\"type\":\"str\"}]}}}}",
    "headers": [
        {"key": "Authorization", "value": "Bearer QQYnRFerJTSEcrfB89fw8prOaObmrch8"}
    ]
}

```

- **响应示例**：

```json
{
    "code": "success",
    "data": {},
    "message": "更新自定义 API 工具提供者成功"
}
```

### 2.9 获取指定 API 工具提供者信息

- **接口说明**：根据传递的工具提供者 id 获取对应的工具提供者详细信息。
- **接口信息**: `授权` + `GET:/api-tools/:provider_id`
- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 ||
| --- | --- | --- | --- | ---|
| provider_id | uuid | 是 | 路由参数，需要获取的 API 工具提供商 id，类型为 uuid。 ||

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 | |
| --- | --- | --- | --- |
| id | uuid | 当前工具提供者对应的 id。 | |
| name | string | 工具提供者的名称。 | |
| icon | string | 工具提供者的 icon 图标。 | |
| openapi_schema | str | OpenAPI-Schema 规范的 JSON 字符串。 | |
| headers | list | 工具提供者的请求头信息。 | |
| | key | string | 请求头的 key。 |
| | value | string | 请求头的 value。 |
| created_at | int | 工具提供者的创建时间。 | |

- **请求示例**：

```shell
GET:/api-tools/e1baf52a-1be2-4b93-ad62-6fad72f1ec37
```

- **响应示例**：

```json
{
    "code": "success",
    "data": {
        "id": "46db30d1-3199-4e79-a0cd-abf12fa6858f",
        "name": "高德工具包",
        "icon": "https://cdn.imooc.com/google.png",
        "openapi_schema": "{\"description\":\"这是一个查询对应英文单词字典的工具\",\"server\":\"https://dict.youdao.com\",\"paths\":{\"/suggest\":{\"get\":{\"description\":\"根据传递的单词查询其字典信息\",\"operationId\":\"YoudaoSuggest\",\"parameters\":[{\"name\":\"q\",\"in\":\"query\",\"description\":\"要检索查询的单词，例如love/computer\",\"required\":true,\"type\":\"str\"},{\"name\":\"doctype\",\"in\":\"query\",\"description\":\"返回的数据类型，支持json和xml两种格式，默认情况下json数据\",\"required\":false,\"type\":\"str\"}]}}}}",
        "headers": [
            {
                "key": "Authorization",
                "value": "Bearer QQYnRFerJTSEcrfB89fw8prOaObmrch8"
            }
        ],
        "created_at": 1721460914
    },
    "message": ""
}
```

### 2.10 获取指定 API 工具信息

- **接口说明**：根据传递的工具提供者 id + 工具的名称查看自定义 API 插件的相关信息，如果没有找到则返回 404 信息。
- **接口信息**: `授权` + `GET:/api-tools/:provider_id/tools/:tool_name`
- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| provider_id | uuid | 是 | 路由参数，需要获取的 API 工具提供商 id，类型为 uuid。 |
| tool_name | string | 是 | 路由参数，需要获取的 API 工具名称。 |

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 | | | |
| --- | --- | --- | --- | ---|---|
| id | uuid | 工具的 id。 | | | |
| description | string | 工具的描述信息。 | | | |
| name | string | 对应工具的名称（OperationId，操作 id）。 | | | |
| inputs | list | 工具的输入信息，类型为列表。 | | | |
| | name | string | 参数名称。 | | |
| | description | string | 参数描述。 | | |
| | required | bool | 是否必填。 | | |
| | type | string | 参数类型。 | | |
| provider | dict | 该工具所属的提供商对应的信息字典。 | | | |
| | name | string | 提供商的名称。 | | |
| | id | uuid | 提供商的 id。 | | |
| | icon | string | 提供商的 icon 图标。 | | |
| | description | string | 提供商的描述信息。 | | |
| | headers | list | 提供商的请求头信息。 | | |
| | | key | string | 请求头的 key。 | | |
| | | value | string | 请求头的 value。 | | |

- **请求示例**：

```shell
GET:/api-tools/46db30d1-3199-4e79-a0cd-abf12fa6858f/tools/GetCurrentName
```

- **响应示例**：

```json
{
    "code": "success",
    "data": {
        "id": "d400cec0-892f-49ab-8f72-821b88c1aaa9",
        "name": "GetCurrentWeather",
        "description": "根据传递的城市名获取指定城市的天气预报，例如：广州。",
        "inputs": [
            {
                "type": "str",
                "required": true,
                "name": "query",
                "description": "需要搜索的查询语句"
            }
        ],
        "provider": {
            "id": "46db30d1-3199-4e79-a0cd-abf12fa6858f",
            "name": "高德工具包",
            "icon": "https://cdn.imooc.com/gaode.png",
            "description": "查询ip所在地、天气预报、路线规划等高德工具包",
            "headers": [
                {"key": "Authorization", "value": "Bearer QQYnRFerJTSEcrfB89fw8prOaObmrch8"}
            ],
            "created_at": 1721460914
        }
    },
    "message": ""
}
```

### 2.11 校验 OpenAPI 字符串是否正确

- **接口说明**：用于校验传递的 OpenAPI-Schema 规范的 JSON 字符串是否正确，如果正确则返回 success，否则返回错误信息。
- **接口信息**: `授权` + `POST:/api-tools/validate-openapi-schema`
- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| openapi_schema | str | 是 | 需要校验的 openapi-schema 字符串，该字符串的规则符合项目 OpenAPI-Schema 规范，该接口只校验数据是否符合规则，不校验对应的提供商名字、工具名字等是否唯一。 |

- **请求示例**：

```json
{
    "openapi_schema": "{\"description\":\"这是一个查询对应英文单词字典的工具\",\"server\":\"https://dict.youdao.com\",\"paths\":{\"/suggest\":{\"get\":{\"description\":\"根据传递的单词查询其字典信息\",\"operationId\":\"YoudaoSuggest\",\"parameters\":[{\"name\":\"q\",\"in\":\"query\",\"description\":\"要检索查询的单词，例如love/computer\",\"required\":true,\"type\":\"str\"},{\"name\":\"doctype\",\"in\":\"query\",\"description\":\"返回的数据类型，支持json和xml两种格式，默认情况下json数据\",\"required\":false,\"type\":\"str\"}]}}}}"
}
```

- **响应示例**：

```json
{
    "code": "success",
    "data": {},
    "message": "OpenAPI-Schema 校验成功"
}
```

```json
{
    "code": "validate_error",
    "data": {},
    "message": "openapi-schema校验失败，info不能为空"
}

```

## 文件模块

### 3.1 将文件上传到腾讯云 COS

- **接口说明**：将文件上传到腾讯云对象存储中，该接口主要用于上传文件，调用接口后返回对应的文件 id、名字、云端位置等信息，主要用于知识库、工具、多模态应用对话。
- **接口信息**: `授权` + `POST:/upload-files/file`
- **请求参数**：
  
| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| file | file | 是 | 需要上传的文件，最多支持上传一个文件，最大支持的文件不能超过 15 MB|

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 |
| --- | --- | --- |
| id | uuid | 上传文件的引用 id，类型为 uuid，在知识库模块、应用对话模块会使用该引用文件 id。 |
| account_id | uuid | 该文件所归属的账号 id，用于标记是哪个账号上传了该文件。 |
| name | string | 原始文件名字。 |
| key | string | 云端文件对应的 key 或者路径。 |
| size | int | 文件大小，单位为字节。 |
| extension | string | 文件扩展名。例如 .md |
| mime_type | string | 文件 mime-type 类型推断。|
| created_at | string | 文件上传时间戳。 |

- **响应示例**：

```json
{
    "code": "success",
    "data": {
        "id": "46db30d1-3199-4e79-a0cd-abf12fa6858f",
        "account_id": "e1baf52a-1be2-4b93-ad62-6fad72f1ec37",
        "name": "项目API文档.md",
        "key": "2024/05/14/218e5217-ab10-4634-9681-022867955f1b.md",
        "size": 30241,
        "extension": ".md",
        "mime_type": "txt",
        "created_at": 1721460914
    },
    "message": ""
}
```

### 3.2 将图片上传到腾讯云cos

- **接口说明**：将图片上传到腾讯云 cos 对象存储中，该接口用于需要上传图片的模块，接口会返回图片的 URL 地址。
- **接口信息**: `授权` + `POST:/upload-files/image`
- **请求参数**：

| 参数名称 | 参数类型 | 是否必须 | 参数说明 |
| --- | --- | --- | --- |
| file | File | 是 | 需要上传的图片文件，支持上传 jpg、jpeg、png、gif，最大不能超过 15 MB。|

- **响应参数**：

| 参数名称 | 参数类型 | 参数说明 |
| --- | --- | --- |
| image_url | string | 上传图片的 URL 地址。 |

- **响应示例**：

```json
{
    "code": "success",
    "data": {
        "image_url": "https://cdn.imooc.com/2024/05/14/218e5217-ab10-4634-9681-022867955f1b.jpg"
    },
    "message": ""
}
```