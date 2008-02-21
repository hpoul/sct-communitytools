# link list models ..

from sphene.sphlinklist.categorytype import doinit

doinit()

from django.db import models

from sphene.sphboard.models import Category, Post

"""
class LinkListCategoryConfig(models.Manager):
    category = models.ForeignKey( Category, unique = True )

    class Admin:
        pass
"""


class LinkListPostExtension(models.Model):
    post = models.ForeignKey( Post, unique = True )
    link = models.URLField( )
