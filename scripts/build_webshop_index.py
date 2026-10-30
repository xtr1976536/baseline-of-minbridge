"""在完整商品集上执行作者的文档转换程序。"""
import os, runpy, sys
from pathlib import Path
from webshop_runtime import configure_products

ROOT=Path(__file__).resolve().parents[1]
u=ROOT/'.local/WebShop'
sys.path.insert(0,str(u))
configure_products(u)
os.chdir(u/'search_engine')
for name in ['resources','resources_100','resources_1k','resources_100k']:
    Path(name).mkdir(exist_ok=True)
runpy.run_path('convert_product_file_format.py',run_name='__main__')
