"""启动官方 WebShop HTML 服务，仅绑定本机；完整商品集为默认。"""
import argparse, json, os, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--demo',action='store_true',help='仅调试 1,000 商品；禁止报告为论文主实验')
p.add_argument('--port',type=int,default=3000)
a=p.parse_args()
u=ROOT/'.local/WebShop'
os.chdir(u);sys.path.insert(0,str(u))
from webshop_runtime import configure_products
configure_products(u,demo=a.demo)
from web_agent_site import utils
from web_agent_site import app as official
print(json.dumps({'source_commit':'64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd',
                  'demo_only':a.demo,'products':utils.DEFAULT_FILE_PATH,
                  'attributes':utils.DEFAULT_ATTR_PATH,'host':'127.0.0.1','port':a.port}))
official.app.run(host='127.0.0.1',port=a.port,debug=False,use_reloader=False)
