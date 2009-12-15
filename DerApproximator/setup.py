#! /usr/bin/env python

descr   = """
"""

from os.path import join
import os
import sys, compileall

DISTNAME            = 'DerApproximator'
DESCRIPTION         = 'A python module for finite-differences derivatives approximation'
LONG_DESCRIPTION    = descr
MAINTAINER          = 'Dmitrey Kroshko',
MAINTAINER_EMAIL    = 'dmitrey-at-openopt-dot-org',
URL                 = 'http://openopt.org',
LICENSE             = 'new BSD'

from __init__ import __version__ as Ver

DOWNLOAD_URL        = 'http://openopt.org/images/7/71/DerApproximator0.17.zip'

try:
    import setuptools
except:
    print('you should have setuptools installed (http://pypi.python.org/pypi/setuptools), for some Linux distribs you can get it via [sudo] apt-get python-setuptools')
import string, shutil
from distutils.errors import DistutilsError
#from numpy.distutils.system_info import system_info, NotFoundError, dict_append, so_ext
from numpy.distutils.core import setup, Extension
import os, sys

DOC_FILES = []

def configuration(parent_package='',top_path=None, package_name=DISTNAME):
    if os.path.exists('MANIFEST'): os.remove('MANIFEST')
    pkg_prefix_dir = '' #'openopt'

    # Get the version

    from numpy.distutils.misc_util import Configuration
    config = Configuration(package_name,parent_package,top_path,
        version     = Ver,
        maintainer  = MAINTAINER,
        maintainer_email = MAINTAINER_EMAIL,
        description = DESCRIPTION,
        license = LICENSE,
        url = URL,
        download_url = DOWNLOAD_URL,
        long_description = LONG_DESCRIPTION)


    # XXX: once in SVN, should add svn version...
    #print config.make_svn_version_py()

    # package_data does not work with sdist for setuptools 0.5 (setuptools bug),
    # so we need to add them here while the bug is not solved...

    return config


if __name__ == "__main__":
    # setuptools version of config script

    # package_data does not work with sdist for setuptools 0.5 (setuptools bug)
    # So we cannot add data files via setuptools yet.

    #data_files = ['test_data/' + i for i in TEST_DATA_FILES]
    #data_files.extend(['docs/' + i for i in doc_files])
    setup(configuration = configuration,
        install_requires='numpy', # can also add version specifiers   #namespace_packages=['kernel'],
        #py_modules = ['kernel', 'tests', 'examples', 'solvers'],
        packages=setuptools.find_packages(),
        include_package_data = True,
        #package_data = '*.txt',
        test_suite='',#"openopt.tests", # for python setup.py test
        zip_safe=True, #False, # the package can run out of an .egg file
        #FIXME url, download_url, ext_modules
        classifiers =
            [ 'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Intended Audience :: Developers',
              'Intended Audience :: Science/Research',
              'License :: OSI Approved :: BSD License',
              'Topic :: Scientific/Engineering']
    )
