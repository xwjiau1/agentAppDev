"""
项目命令行入口（CLI）。

基于 click 库封装了整个 RAG 流程的 5 个子命令：
  download-models    下载 Docling PDF 解析所需的模型
  parse-pdfs         将 PDF 年报解析为结构化 JSON（支持多进程并行）
  serialize-tables   调用 LLM 将解析出的表格序列化为上下文独立的信息块
  process-reports    对解析结果执行后续预处理（规整 -> Markdown -> 分块 -> 建向量库）
  process-questions  读取问题文件，执行检索 + LLM 回答，输出答案 JSON

用法（必须在包含数据的目录下运行，例如 data/test_set/）：
  cd data/test_set
  python ../../main.py process-questions --config max_nst_o3m
"""
import click
from pathlib import Path
from src.pipeline import Pipeline, configs, preprocess_configs

# click.group 表示这是一个命令组，下面用 @cli.command() 注册子命令
@click.group()
def cli():
    """Pipeline command line interface for processing PDF reports and questions."""
    pass

@cli.command()
def download_models():
    """Download required docling models."""
    click.echo("Downloading docling models...")
    Pipeline.download_docling_models()

@cli.command()
@click.option('--parallel/--sequential', default=True, help='Run parsing in parallel or sequential mode')
@click.option('--chunk-size', default=2, help='Number of PDFs to process in each worker')
@click.option('--max-workers', default=10, help='Number of parallel worker processes')
def parse_pdfs(parallel, chunk_size, max_workers):
    """Parse PDF reports with optional parallel processing."""
    # root_path 取当前工作目录（cwd），因此需要在数据目录下运行本脚本
    root_path = Path.cwd()
    pipeline = Pipeline(root_path)
    
    click.echo(f"Parsing PDFs (parallel={parallel}, chunk_size={chunk_size}, max_workers={max_workers})")
    pipeline.parse_pdf_reports(parallel=parallel, chunk_size=chunk_size, max_workers=max_workers)

@cli.command()
@click.option('--max-workers', default=10, help='Number of workers for table serialization')
def serialize_tables(max_workers):
    """Serialize tables in parsed reports using parallel threading."""
    # 表格序列化较慢，内部使用线程池 + 异步 LLM 请求加速
    root_path = Path.cwd()
    pipeline = Pipeline(root_path)
    
    click.echo(f"Serializing tables (max_workers={max_workers})...")
    pipeline.serialize_tables(max_workers=max_workers)

@cli.command()
@click.option('--config', type=click.Choice(['ser_tab', 'no_ser_tab']), default='no_ser_tab', help='Configuration preset to use')
def process_reports(config):
    """Process parsed reports through the pipeline stages."""
    # preprocess_configs 只控制是否使用序列化表格（影响输出目录带 _ser_tab 后缀）
    root_path = Path.cwd()
    run_config = preprocess_configs[config]
    pipeline = Pipeline(root_path, run_config=run_config)
    
    click.echo(f"Processing parsed reports (config={config})...")
    pipeline.process_parsed_reports()

@cli.command()
@click.option('--config', type=click.Choice(['base', 'pdr', 'max', 'max_no_ser_tab', 'max_nst_o3m', 'max_st_o3m', 'ibm_llama70b', 'ibm_llama8b', 'gemini_thinking']), default='base', help='Configuration preset to use')
def process_questions(config):
    """Process questions using the pipeline."""
    # configs 中的每个配置决定了：是否父文档检索、是否 LLM 重排、
    # 并行请求数、API 提供商、回答模型等关键参数
    root_path = Path.cwd()
    run_config = configs[config]
    pipeline = Pipeline(root_path, run_config=run_config)
    
    click.echo(f"Processing questions (config={config})...")
    pipeline.process_questions()

if __name__ == '__main__':
    cli()