# Path路径对象与相对路径

> 复习优先级：必背。先记结论，再用案例解释“这行代码做了什么、有哪些边界”。

## 面试速记

Path是路径对象；`/`可拼接路径，exists、is_file、glob等检查或遍历路径。相对路径通常依赖当前工作目录，不自动相对源码所在目录。

## 面试问答

**问：如何相对脚本定位资源？** 通常从Path(__file__).resolve().parent拼接；交互环境可能没有__file__。

**问：resolve后就能保证安全访问吗？** 不能，仍需验证路径位于允许目录；软链接与并发变化也可能影响访问。

## 实际案例与代码

[企业报告问答与回归评估](../../应用侧/知识问答与文档处理/企业报告问答与回归评估/案例说明.md) · [main.py，38–42行](../../应用侧/知识问答与文档处理/企业报告问答与回归评估/main.py#L38-L42)

以下为当前仓库原代码，统一去除外层缩进；它是源码节选，不是独立运行程序。

```python
root_path = Path.cwd()
pipeline = Pipeline(root_path)

click.echo(f"Parsing PDFs (parallel={parallel}, chunk_size={chunk_size}, max_workers={max_workers})")
pipeline.parse_pdf_reports(parallel=parallel, chunk_size=chunk_size, max_workers=max_workers)
```

入口显式把cwd作为数据根目录，所以必须从正确数据目录运行。它不是main.py所在目录；移动脚本不自动移动数据根。

## 易错点与追问

配置型数据根目录和源码目录是两种不同约定，不能混用。不要把字符串连接的路径写死为某一种系统分隔符。
