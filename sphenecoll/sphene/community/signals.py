import django.dispatch
# Called when the edit_profile view initializes the form ...
# gives listeners a chance to add custom fields to the form.
profile_edit_init_form = django.dispatch.Signal()

# Called when the edit_profile view has validated the form data and has
# saved the profile data. - Gives listeners a chance to save their form
# data previously added in profile_edit_init_form
profile_edit_save_form = django.dispatch.Signal()

# called when the profile view displays the profile of a given user.
# Listeners should return HTML code which will be added into the
# 2 column html table of the profile.
# Arguments:
#  - request (Containing the http request)
#  - user (The User from whom to display the profile.)
profile_display = django.dispatch.Signal()


# A signal which can be used to do periodic work,
# e.g. the board could recalculate the heat of threads.
# Should be called once a day.
maintenance = django.dispatch.Signal()



# This method should be regularly called (once a day) through a cron job like:
#
# echo -e "from sphene.community.signals import trigger_maintenance\ntrigger_maintenance()" | ./manage.py shell --plain
def trigger_maintenance():
    maintenance.send(None)
