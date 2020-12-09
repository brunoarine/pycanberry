# -*- coding: utf-8 -*-
"""
Created on Mon Apr 24 09:37:37 2017

@author: LARE
"""
import subprocess

def execute(command):
    error_num = subprocess.call(command, shell=True)
    return error_num
    