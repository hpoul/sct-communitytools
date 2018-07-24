from django.utils.text import slugify as django_slugify


def slugify(s, entities=True, decimal=True, hexadecimal=True, model=None, slug_field='slug', pk=None):
    # we don't want a string > 40 characters
    if len(s) > 40:
        s = s[:40]

    s = django_slugify(s)

    slug = s
    if model:  
        # return unique slug for a model (appending integer counter)
        def get_query():
            query = model.objects.filter(**{ slug_field: slug })
            if pk:
                query = query.exclude(pk=pk)
            return query
        counter = 2
        while get_query():
            slug = "%s-%s" % (s, counter)
            counter += 1
    return slug
