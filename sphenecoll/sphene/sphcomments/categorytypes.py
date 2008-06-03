from sphene.sphboard.categorytypes import DefaultCategoryType
from sphene.sphboard.categorytyperegistry import CategoryType


class CommentsCategoryType(DefaultCategoryType):
    """
    Defines the "root" category for comments.
    """
    name = 'sphcomments'
    label = 'Comments Category'

    def is_displayed(self):
        return False


class CommentsOnObjectCategoryType(DefaultCategoryType):
    name = 'sphcommentsonobject'
    label = 'Comments On Object (Do not create this by hand.)'

    def get_absolute_url_for_category(self):
        url = None
        try:
            url = self.category.sphcomments_config.get() \
                .content_object.get_absolute_url()
            if not url:
                url = None
        except:
            pass
        return url


