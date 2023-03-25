import os, re

def config(name, default=None, glob=False) :
    return os.environ.get((("GLOBAL" if glob else re.compile(r'[^0-9a-z_]+', re.I).sub('_', os.path.basename(__file__))) + '_' + name).upper(), default)
