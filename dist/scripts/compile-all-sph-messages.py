#!/usr/bin/python


## Very simple script to compile all language files for all
## SCT apps.

#from django.bin.compile-messages import compile_messages
c = __import__('django.bin.compile-messages', None, None, 'compile_messages')

import os

olddir = os.getcwd()

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.join(ROOT_PATH,'../..')

sphapps = ( 'community',
            'sphboard',
            'sphwiki',
            'sphlinklist',
            'sphblog',
            )

for app in sphapps:
    os.chdir( os.path.join(ROOT_PATH, 'sphenecoll', 'sphene', app ) )
    c.compile_messages()

os.chdir( olddir )

