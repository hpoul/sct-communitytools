from django.urls import re_path

from sphene.sphsearchboard.views import view_search_posts

urlpatterns = [re_path(r'^$', view_search_posts, name='sphsearchboard_posts')]

