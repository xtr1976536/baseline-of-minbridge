"""Keep the user-supplied gateway credential encrypted with Windows DPAPI.

No credential appears in command-line arguments, source, or emitted output.
"""
from pathlib import Path
import ctypes
from ctypes import wintypes
import getpass
import os
import sys

PATH=Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local'))/'CodexCredentials/verifin-aiwanwu.dpapi'

class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]

def crypt(data,decrypt=False):
    if os.name!='nt':raise RuntimeError('DPAPI storage requires Windows; use an environment variable on other systems')
    buffer=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)))
    output=Blob()
    if decrypt:
        ok=ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(output))
    else:
        ok=ctypes.windll.crypt32.CryptProtectData(ctypes.byref(source),'VeriFin gateway',None,None,None,1,ctypes.byref(output))
    if not ok:raise ctypes.WinError()
    try:return ctypes.string_at(output.data,output.size)
    finally:ctypes.windll.kernel32.LocalFree(output.data)

def load():
    return crypt(PATH.read_bytes(),decrypt=True).decode('utf-8')

if __name__=='__main__':
    value=getpass.getpass('Gateway API key: ').strip()
    if not value:raise SystemExit('No credential supplied')
    PATH.parent.mkdir(parents=True,exist_ok=True)
    PATH.write_bytes(crypt(value.encode('utf-8')))
    assert load()==value
    print('Credential stored with Windows DPAPI; plaintext was not saved.')
