"""仅降低原始商品 JSON 的加载峰值；仍使用作者的字段清理和处理函数。"""
import json
import gc
import sys
from pathlib import Path


def configure_products(root, demo=False):
    # Parsed JSON contains no cycles; reference counting still frees objects.
    # Repeated cyclic-GC scans over >1M products otherwise cause heavy swapping.
    gc.disable()
    import ijson
    from web_agent_site import utils
    if not demo:
        utils.DEFAULT_FILE_PATH=str(root/'data/items_shuffle.json')
        utils.DEFAULT_ATTR_PATH=str(root/'data/items_ins_v2.json')
    from web_agent_site.engine import engine
    original_json=engine.json

    class StreamingProductJson:
        def __getattr__(self,name):
            return getattr(original_json,name)

        def load(self,fp,*args,**kwargs):
            if Path(fp.name).resolve()==Path(utils.DEFAULT_FILE_PATH).resolve():
                # Author load_products immediately calls clean_product_keys.
                # Applying the same function per item avoids retaining unused
                # scraped fields and the entire 5.48 GB JSON text in memory.
                old_print=engine.print
                engine.print=lambda *a,**k: None
                try:
                    return [{sys.intern(k):v for k,v in engine.clean_product_keys([p])[0].items()}
                            for p in ijson.items(fp,'item',use_float=True)]
                finally:
                    engine.print=old_print
            return original_json.load(fp,*args,**kwargs)

    engine.json=StreamingProductJson()
    return engine
