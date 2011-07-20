1. Run:
$ python bootstrap.py
$ bin/buildout
$ bin/django syncdb
$ bin/django runserver

2. Visit http://localhost:8000

3. South
South is included in buildout.cfg but it is not enabled in 
sph_project/settings.py

If you want to use South then:

3.1. Uncomment line containing 'south' in settings.py
3.2. Assuming you have no database generated yet run:
  $ bin/django syncdb (do NOT create superuser as this will fail 
                       at this moment due to bug in Django)
  $ bin/django migrate
  $ bin/django createsuperuser
  $ bin/django runserver
  
4. Development
You may use this project as a template for your. To do it you may call svn export like:

svn export http://source.sphene.net/svn/root/django/communitytools/trunk/sphenecoll/sphene my_new_project
  
5. Other
 If you want to use postgresql as database and/or Djapian (required by sphsearchboard) then simply
 extend buildout.cfg by adding new eggs or recipes like:
 
(...)
 
[django]
recipe = djangorecipe
eggs =
    PIL
    south
    pycrypto
    Djapian
    psycopg2
    
(...)