from __future__ import print_function
from future.builtins import input
try:
    import setuptools
except:
    print('you should have setuptools installed (http://pypi.python.org/pypi/setuptools), for some Linux distribs you can get it via [sudo] apt-get install python-setuptools')
    print('press Enter for exit...')
    eval(input())
    exit()

import os, sys
(filepath, filename) = os.path.split(__file__)

for moduleName in ['DerApproximator', 'FuncDesigner', 'OpenOpt', 'SpaceFuncs']:
    print(moduleName + ' in-place installation:')
    os.chdir(((filepath + os.sep) if filepath != '' else '') + moduleName) 
    os.system('\"%s\" setup.py develop' % sys.executable)
    #os.system('%s setup.py develop' % sys.executable)
    os.chdir('..')
