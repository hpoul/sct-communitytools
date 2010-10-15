1. Run:
$ python bootstrap.py
$ bin/buildout
$ bin/django syncdb
$ bin/django runserver

2. Visit http://localhost:8000

This setup contains references to Djapian module. If you don't want
use Djapian for searching, or have some dependency problems, you may
remove line containing word Djapian from buildout.cfg

3. South
South is included in buildout.cfg but it is not enabled in 
sph_project/settings.py

If you want to use South then:

1. Uncomment line containing 'south' in settings.py
2. Assuming you have no database generated yet run:
  $ bin/django syncdb (do NOT create superuser as this will fail 
                       at this moment due to bug in Django)
  $ bin/django migrate
  $ bin/django createsuperuser
  $ bin/django runserver