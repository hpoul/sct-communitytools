
# Called when the edit_profile view initializes the form ...
# gives listeners a chance to add custom fields to the form.
profile_edit_init_form = object()

# Called when the edit_profile view has validated the form data and has
# saved the profile data. - Gives listeners a chance to save their form
# data previously added in profile_edit_init_form
profile_edit_save_form = object()

# called when the profile view displays the profile of a given user.
# Listeners should return HTML code which will be added into the
# 2 column html table of the profile.
# Arguments:
#  - request (Containing the http request)
#  - user (The User from whom to display the profile.)
profile_display = object()
