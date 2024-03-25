#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   main.py
@Time    :   2023/09/26 08:04:35
@Author  :   Jason XU 
@Version :   1.0
@Desc    :   None
'''

import streamlit.web.cli as stcli
import sys,os

def resolve_path(rela_path):
    abs_path = os.path.abspath(os.path.join(os.getcwd(),rela_path))
    return abs_path

def main():
    sys.argv=[
        "streamlit",
        "run",
        resolve_path("./ab_app_streamlit.py"),
        # "--global.developmentMode=false"
    ]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()