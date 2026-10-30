"""下载公开镜像，核对内容 hash；不将大型商品数据提交 Git。"""
import hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.local/WebShop/data';OUT.mkdir(parents=True,exist_ok=True)
REV='ce990fff5aee388db2706f07820c578ab68e0453'
BASE=f'https://huggingface.co/datasets/YWZBrandon/webshop-data/resolve/{REV}'
SPECS={
 'items_shuffle.json':(5479720229,'2ef591d65df3af89e972ab72468eb82cbf124d876552d9f3678667edd620a6c8'),
 'items_ins_v2.json':(186295270,'1d36af476bdb8f82a5da62bd8acdabe54cd8de2fa84010d37da5c4890feb447e'),
 'items_human_ins.json':(5137548,None),
}
records=[]
for filename,(size,expected) in SPECS.items():
    target=OUT/filename
    if not target.exists() or target.stat().st_size!=size:
        subprocess.run(['curl','--fail','--location','--retry','3','--continue-at','-',
                        f'{BASE}/{filename}','--output',str(target)],check=True)
    h=hashlib.sha256()
    with target.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    digest=h.hexdigest()
    assert target.stat().st_size==size,(filename,'file length mismatch')
    assert expected is None or digest==expected,(filename,'SHA256 mismatch')
    records.append({'filename':filename,'bytes':size,'sha256':digest,
       'mirror_url':f'{BASE}/{filename}','expected_lfs_sha256':expected,
       'provenance_note':'public mirror; matching Git/LFS object IDs across YWZBrandon and HongbangYuan mirrors; original Google Drive download unavailable'})
    print(filename,size,digest,flush=True)
(ROOT/'manifests/webshop-data.json').write_text(json.dumps(records,indent=2))
