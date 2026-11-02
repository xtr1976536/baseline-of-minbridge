"""Record actual environment interactions, without changing observations or rewards."""
import json

def serializable(value):
    return value.tolist() if hasattr(value,'tolist') else str(value)

def trace_environment(env,path):
    for name in ('reset','step'):
        if not hasattr(env,name):continue
        original=getattr(env,name)
        def logged(*args,_original=original,_name=name,**kwargs):
            try:
                result=_original(*args,**kwargs)
            except Exception as ex:
                with path.open('a') as stream:
                    stream.write(json.dumps({'method':_name,'args':args,'kwargs':kwargs,'error':type(ex).__name__+': '+str(ex)},ensure_ascii=False,default=serializable)+'\n')
                raise
            with path.open('a') as stream:
                stream.write(json.dumps({'method':_name,'args':args,'kwargs':kwargs,'result':result},ensure_ascii=False,default=serializable)+'\n')
            return result
        setattr(env,name,logged)
    return env


def trace_webshop_episodes(namespace,path):
    original=namespace['webshop_run']
    def logged(session,prompt,to_print=True):
        reward=original(session,prompt,to_print=to_print)
        with path.open('a') as stream:
            stream.write(json.dumps({'session':session,'reward':reward,'success':reward==1},default=serializable)+'\n')
        return reward
    namespace['webshop_run']=logged


def safe_wikipedia_cleaner(original):
    def clean(text):
        try:return original(text)
        except UnicodeError:
            # BeautifulSoup has already returned Unicode text; do not reinterpret
            # literal backslashes as Python escapes or replace its factual content.
            return text
    return clean
