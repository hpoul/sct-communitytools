#
# Setup file for Sphene Community Tools
# Provided by Dennis @ allymbrain.com:
# http://allmybrain.com/2009/10/21/the-python-install-system-needs-an-overhaul/
#

import os
from setuptools import setup, find_packages
from finddata import find_package_data
 
packages=find_packages('sphenecoll')
package_data=find_package_data('sphenecoll')
static = find_package_data('static','sphene')
# not in correct format
static_dict={} # dir -> files
for path in static['sphene']:
   dir, file = os.path.split(path)
   dir = os.path.join('static', dir )
   files = static_dict.setdefault( dir, [] )
   files.append(os.path.join('static',path))
 
setup(
 name='Sphene Community Tools',
 version='0.6',
 author = 'Herbert Poul',
 author_email = 'herbert.poul@gmail.com',
 url = 'http://sct.sphene.net/',
 description = 'SCT (Sphene Community Tools) is a collection of Django applications. It currently consists of a Wiki and Forum application which are applicable for communities, support forums, blogs, etc.',
 long_description = '''SCT (Sphene Community Tools) is a collection of Django applications that are
designed to be easily pluggable into any Django project. It currently consists
of a Wiki and a Forum application. It contains an example project that allows
users to create a community Web site containing the Wiki and Board applications
without any further coding/configuration changes.''',


 packages=packages,
 package_data=package_data,
 package_dir={'sphene':'sphenecoll/sphene'},
 # these scripts are only required before creating distribution... no need to install them.
 #scripts=['dist/scripts/make-messages.py', 'dist/scripts/compile-all-sph-messages.py' ],
 data_files=static_dict.items()
)

