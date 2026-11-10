import os, re, inspect

def config(name: str, default:str|None=None, glob:bool=False) -> str : 
    prefix = "GLOBAL" if glob else re.compile(r'[^0-9a-z_]+', re.I).sub('_', os.path.basename(inspect.stack()[1].filename))
    res = os.environ.get((prefix + '_' + name).upper(), default)
    assert res is not None, f"No value for config {name} and no default provided"
    return res
