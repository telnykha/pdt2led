__author__ = 'FiksII'
# -*- coding: utf-8 -*-
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages=["win32com", "pythoncom","win32com.gen_py"], includes=["win32com"], excludes=[])

import sys
base = 'Win32GUI' if sys.platform=='win32' else None
# base = None


executables = [
    Executable('Main.py', targetName="Fluovisor.exe", base=base)
]

setup(
    name=u'Флуовизор',
    version='3.0',
    description=u'Программа для обработки данных с флуовизора',
    options=dict(build_exe=buildOptions),
    executables=executables, requires=['PyQt4']
)
