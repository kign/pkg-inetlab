import os, re, inspect

def config(name, default=None, glob=False) :
    prefix = "GLOBAL" if glob else re.compile(r'[^0-9a-z_]+', re.I).sub('_', os.path.basename(inspect.stack()[1].filename))
    return os.environ.get((prefix + '_' + name).upper(), default)
