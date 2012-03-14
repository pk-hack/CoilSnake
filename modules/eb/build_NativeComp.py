from distutils.core import setup, Extension

module1 = Extension('NativeComp', sources = ['NativeComp.c'])

setup(name = 'PackageName',
        version = '1.0',
        description = 'Native package for EB compression routines',
        ext_modules = [module1])
