from django.contrib.syndication.feeds import Feed
from sphene.sphwiki.models import WikiSnipChange, WikiSnip
from sphene.community.middleware import get_current_group

class LatestWikiChanges(Feed):
    title = "Latest Wiki Changes."
    description = "The latest changes and additions to the wiki."
    link = "/wiki/"

    def items(self):
        group = get_current_group()
        return WikiSnipChange.objects.filter( snip__group = group ).order_by( '-edited' )[:10]

    def item_link(self, item):
        group = get_current_group()
        return 'http://' + group.baseurl + item.snip.get_absolute_url()

    def item_pubdate(self, item):
        return item.edited
    

