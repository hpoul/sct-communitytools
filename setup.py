#
# Setup file for Sphene Community Tools
# Provided by Dennis @ allymbrain.com:
# http://allmybrain.com/2009/10/21/the-python-install-system-needs-an-overhaul/
#

#import os
from setuptools import setup, find_packages


CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Natural Language :: German',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.5',
    'Topic :: Communications',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Message Boards',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary',
    'Topic :: Software Development :: Libraries :: Python Modules',

] 

setup(
 name='django-sct',
 version='0.7',
 author = 'Herbert Poul',
 author_email = 'herbert.poul@gmail.com',
 url = 'http://sct.sphene.net/',
 description = 'SCT (Sphene Community Tools) is a collection of Django applications for communities. It currently consists of a Forum and Wiki application which are applicable for communities, support forums, blogs, etc.',
 long_description = '''SCT (Sphene Community Tools) is a collection of Django applications that are
designed to be easily pluggable into any Django project. It currently consists
of a Wiki and a Forum application. It contains an example project that allows
users to create a community Web site containing the Wiki and Board applications
without any further coding/configuration changes.''',
 install_requires=[
    'Django>=1.4',
    'pycrypto>=2.0',
 ],
 classifiers=CLASSIFIERS,
 license='BSD License',


 packages=find_packages('sphenecoll',exclude=['simpleproject','sph_project']),
 include_package_data=True,
 zip_safe = False,
 package_dir={'sphene':'sphenecoll/sphene'},
 # these scripts are only required before creating distribution... no need to install them.
 #scripts=['dist/scripts/make-messages.py', 'dist/scripts/compile-all-sph-messages.py' ],
 #data_files=static_dict.items()
)

