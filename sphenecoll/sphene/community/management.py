
from django.dispatch import dispatcher
from django.db.models import signals, get_apps, get_models
from sphene.community import models

def init_data(app, created_models, verbosity, **kwargs):
    from sphene.community.models import Group, Navigation
    if Group in created_models:
        group = Group( name = 'example',
                       longname = 'Example Group',
                       baseurl = 'www.example.com', )
        group.save()

        if Navigation in created_models:
            nav = Navigation( group = group,
                              label = 'Home',
                              href = '/wiki/show/Start/',
                              urltype = 0,
                              sortorder = 10,
                              navigationType = 0,
                              )
            nav.save()

            nav = Navigation( group = group,
                              label = 'Board',
                              href = '/board/show/0/',
                              urltype = 0,
                              sortorder = 20,
                              navigationType = 0,
                              )
            nav.save()


from django.db import backend, connection, transaction
from sphene.community.models import ApplicationChangelog
from datetime import datetime

def do_changelog(app, created_models, verbosity, **kwargs):
    app_models = get_models( app )
    if app_models == None: return

    sql = ()
    for clazz in app_models:
        changelog = getattr(clazz, 'changelog', None)
        if not changelog: continue
        #changelog = get_changelog(None)

        version = None
        currentversion = changelog[-1][0]
        currentcl = ApplicationChangelog( app_label = clazz._meta.app_label,
                                          model = clazz._meta.object_name.lower(),
                                          version = currentversion,
                                          applied = datetime.today(), )
        try:
            appcl = ApplicationChangelog.objects.filter( app_label = clazz._meta.app_label,
                                                         model = clazz._meta.object_name.lower(), )\
                                                         .latest()
            version = appcl.version
            if currentversion == version:
                continue
        except ApplicationChangelog.DoesNotExist:
            # See if model was just created...
            if clazz in created_models:
                # Store latest version in changelog ...
                currentcl.save()
                continue # No need to do anything ...
            else:
                # We need to do the whole changelog ...
                version = None


        for change in changelog:
            date, changetype, stmt = change
            if version != None and version > date:
                # This change was already applied ...
                continue
            
            if changetype == 'alter':
                sqlstmt = 'ALTER TABLE %s %s' % (backend.quote_name(clazz._meta.db_table), stmt)
                sql += (sqlstmt,)
                print "%s: SQL Statement: %s" % (date, sqlstmt)
            elif changetype == 'update':
                sqlstmt = 'UPDATE %s %s' % (backend.quote_name(clazz._meta.db_table), stmt)
                sql += (sqlstmt,)
                print "%s: SQL Statement: %s" % (date, sqlstmt)
            else:
                print "Unknown changetype: %s - %s" % (changetype, str(change))

        # Store new version ...
        currentcl.save()

    if len(sql) > 0:
        confirm = 'x'
        while confirm not in ('yes', 'no'):
            confirm = raw_input("Detected changes - Do you want to execute SQL Statements ? (yes,no): ")
        if confirm == 'yes':
            curs = connection.cursor()
            for sqlstmt in sql:
                curs.execute( sqlstmt )
            transaction.commit_unless_managed()
        else:
            print "Not updating database. You have to do this by hand !"

dispatcher.connect(init_data, sender=models, signal=signals.post_syncdb)
dispatcher.connect(do_changelog, signal=signals.post_syncdb)

