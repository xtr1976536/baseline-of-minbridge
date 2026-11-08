"""Read-only local live monitor. No API calls, retries, or experiment changes."""
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/gpt56_sol_full'
SCHEDULING=OUT/'scheduling'


def now():return datetime.now(timezone.utc).isoformat()


def write_atomic(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)


def pid_alive(pid):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype=wintypes.BOOL
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    kernel.CloseHandle.restype=wintypes.BOOL
    handle=kernel.OpenProcess(0x1000,False,int(pid))
    if not handle:return False if ctypes.get_last_error()==87 else None
    try:
        code=wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle,ctypes.byref(code)):return None
        return code.value==259
    finally:kernel.CloseHandle(handle)


def signature():
    scope=json.loads((ROOT/'configs/gpt56_sol_scope.json').read_text(encoding='utf-8'))
    files=[OUT/'process_state.json',ROOT/'configs/gpt56_sol_scope.json']
    for name in scope['datasets']:
        files.extend((OUT/'shards'/name).rglob('predictions.jsonl'))
    return tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in files if p.exists())


def refresh():
    result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/progress_full_run.py')],
        cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=30,
        creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:raise RuntimeError('Progress reader failed; retrying next check')
    return json.loads(result.stdout)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--interval',type=float,default=5)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    if args.interval<2:parser.error('interval must be at least two seconds')
    SCHEDULING.mkdir(parents=True,exist_ok=True)
    import msvcrt
    with (SCHEDULING/'live_monitor.lock').open('a+b') as lock:
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:raise SystemExit('A live monitor is already running')
        started=now()
        previous=None
        progress=None
        last_printed=None
        while True:
            try:
                current=signature()
                if progress is None or current!=previous:
                    progress=refresh()
                    previous=current
                worker=json.loads((OUT/'process_state.json').read_text(encoding='utf-8'))
                alive=pid_alive(worker['pid'])
                ended=bool(worker.get('finished_at')) or alive is False
                if ended:progress=refresh()
                errors=sum(d['statuses'].get('error',0) for d in progress['datasets'].values())
                if not ended:status='running'
                elif worker.get('exit_code')==0 and progress['completed']==progress['total']:
                    status='completed_with_errors' if errors else 'completed'
                else:status='interrupted'
                result={'checked_at':now(),'monitor_pid':os.getpid(),'monitor_started_at':started,
                    'interval_seconds':args.interval,'status':status,'worker_pid':worker['pid'],
                    'worker_alive':alive,'worker_exit_code':worker.get('exit_code'),
                    'completed':progress['completed'],'total':progress['total'],'errors':errors,
                    'datasets':progress['datasets'],
                    'results_report':str(OUT/('FinQA_TAT-QA_results.md')),
                    'experiment_changed_by_monitor':False}
                write_atomic(SCHEDULING/'live_monitor_state.json',result)
                lines=['# GBFR 实时进度','',f"检查时间（UTC）：{result['checked_at']}",
                    f"状态：{status}；记录 {progress['completed']} / {progress['total']}；错误 {errors}。",'',
                    '| 数据集 | 已保存记录 | 总数 | 错误 |','|---|---:|---:|---:|']
                for name,d in progress['datasets'].items():
                    lines.append(f"| {name} | {d['completed']} | {d['total']} | {d['statuses'].get('error',0)} |")
                lines+=['','本监控仅读取本地记录，不调用模型或修改实验。结果由实验进程在结束时汇总。']
                target=OUT/'live_progress.md'
                temporary=target.with_suffix('.md.tmp')
                temporary.write_text('\n'.join(lines)+'\n',encoding='utf-8')
                temporary.replace(target)
                marker=(status,progress['completed'],errors)
                if marker!=last_printed:
                    print(json.dumps({k:result[k] for k in ('checked_at','status','completed','total','errors','worker_pid')},ensure_ascii=False),flush=True)
                    last_printed=marker
                if ended or args.once:break
            except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
                print(json.dumps({'checked_at':now(),'monitor_read_error':type(exc).__name__},ensure_ascii=False),flush=True)
                if args.once:raise
                previous=None
            time.sleep(args.interval)


if __name__=='__main__':main()
