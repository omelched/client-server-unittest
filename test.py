import os
import subprocess


def run_in_subproc(path):
    abs_path = os.path.abspath(path)
    cmd = ['python', abs_path]
    p = subprocess.run(cmd, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(p.stdout)
    print(p)


file_path = 'test_ServerExecutor_svr_print.py'
script = \
    """#!/usr/bin/env python
print(\'test\')
"""
file = open(file_path, 'w+')
file.truncate(0)
file.write(script)
print(run_in_subproc(file_path))
file.close()
