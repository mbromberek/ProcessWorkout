'''
BSD 3-Clause License
Copyright (c) 2020, Mike Bromberek
All rights reserved.
'''
# First party classes
import os,glob,shutil
import re

# 3rd party classes
import numpy as np

# Custom Classes

def convert(i):
    '''
    Convert from numpy int and float formats to standard python format
    If type is int64 or float64 it is converted to int or float
    Else it is returned with the same type and value passed
    '''
    if isinstance(i, np.int64):
        return int(i)
    elif isinstance(i, np.float64):
        return float(i)
    else:
        return i
