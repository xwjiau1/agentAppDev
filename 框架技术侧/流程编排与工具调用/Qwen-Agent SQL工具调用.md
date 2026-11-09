# Qwen-Agent SQL工具调用

## 技术实现

通过register_tool注册SQL工具，参数schema描述模型应提交的sql_input，call接收JSON参数后执行查询并返回文本结果。

## 应用思路

将数据库访问封装为工具可接入对话；生产数据访问应由业务层限制语句类型与权限，模型提示词不能替代权限控制。

## 代码解析

### 定义工具参数

[门票订单查询与图表助手](../../应用侧/数据分析与ChatBI/门票订单查询与图表助手/案例说明.md) · [assistant_ticket_bot-1.py，133–145行](../../应用侧/数据分析与ChatBI/门票订单查询与图表助手/assistant_ticket_bot-1.py#L133-L145)

```python
@register_tool('exc_sql')

class ExcSQLTool(BaseTool):

    """

    SQL查询工具，执行传入的SQL语句并返回结果。

    """

    description = '对于生成的SQL，进行SQL查询'

    parameters = [{
```

description帮助模型识别用途；parameters指定sql_input为必填字符串。工具名需与Assistant.function_list一致。

### 执行并返回结果

[门票订单查询与图表助手](../../应用侧/数据分析与ChatBI/门票订单查询与图表助手/案例说明.md) · [assistant_ticket_bot-1.py，159–174行](../../应用侧/数据分析与ChatBI/门票订单查询与图表助手/assistant_ticket_bot-1.py#L159-L174)

```python
def call(self, params: str, **kwargs) -> str:

    import json

    args = json.loads(params)

    sql_input = args['sql_input']

    database = args.get('database', 'ubr')

    # 创建数据库连接

    engine = create_engine(

        f'mysql+mysqlconnector://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:3306/{database}?charset=utf8mb4',
```

json.loads解析参数；create_engine配置连接池；read_sql执行原始SQL，head(10)只限制展示数量，不限制数据库实际扫描或语句权限。

## 应用方式差异

编号版本分别添加图表生成和展示方式，工具注册机制相同，不重复解释。
