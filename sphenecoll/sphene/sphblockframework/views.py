
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext

from sphene.community.middleware import get_current_group
from sphene.community.sphutils import sph_reverse

from sphene.sphblockframework import blockregistry
from sphene.sphblockframework.models import \
    get_or_create_page_configuration, \
    get_or_create_region, \
    BlockConfiguration, \
    BlockInstancePosition, \
    PageConfiguration, \
    PageConfigurationInstance




class CreateBlockForm(forms.ModelForm):
    class Meta:
        model = BlockConfiguration
        exclude = ('page_configuration',)


def config(request, group):
    blockconfigs = BlockConfiguration.objects.filter( page_configuration__group = group )

    if request.method == 'POST' and 'createblockconfig' in request.POST:
        createblockform = CreateBlockForm(request.POST)
        if createblockform.is_valid():
            data = createblockform.cleaned_data
            
            page_config = get_or_create_page_configuration(group)
            block_config = createblockform.save(commit = False)
            block_config.page_configuration = page_config
            block_config.save()

            createblockform = CreateBlockForm()
            #block_config = BlockConfiguration(page_configuration = page_config,
            #                                  label = data['label'],
            #                                  block_name = data[
    else:
        createblockform = CreateBlockForm()

    return render_to_response('sphene/sphblockframework/config.html',
                              { 'blockconfigs': blockconfigs,
                                'createblockform': createblockform,
                                },
                              context_instance = RequestContext(request))

def edit_block_config(request, group, block_config_id):
    if request.method == 'GET' and 'delete' in request.GET:
        BlockConfiguration.objects.get( pk = block_config_id ).delete()
        return HttpResponseRedirect( sph_reverse( 'sphblockframework_config' ) )

    return None

def useasdefault(request, group):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Exception

    page_config = get_or_create_page_configuration(group)
    try:
        pciuser = PageConfigurationInstance.objects.get(
            page_configuration = page_config,
            user = request.user )
    except PageConfigurationInstance.DoesNotExist:
        # Nothing to do ..
        raise Exception

    try:
        pcidefault = PageConfigurationInstance.objects.get(
            page_configuration = page_config,
            user__isnull = True )

        pcidefault.delete()
    except PageConfigurationInstance.DoesNotExist:
        pass

    pciuser.user = None
    pciuser.save()

    return HttpResponseRedirect(request.GET['next'])


def reverttodefault(request, group):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise Exception
    
    page_config = PageConfiguration.objects.get(group = group)
    try:
        PageConfigurationInstance.objects.get(
            page_configuration = page_config,
            user = request.user).delete()
    except PageConfigurationInstance.DoesNotExist:
        # nothing to do ..
        pass

    return HttpResponseRedirect(request.GET['next'])


def addblock(request, group):
    region_name = request.POST['region']
    region = get_or_create_region(group, request.user, region_name)
    try:
        lastblock = BlockInstancePosition.objects.filter(region = region).\
            order_by('-sortorder')[0]
        sortorder = lastblock.sortorder + 1
    except IndexError:
        sortorder = 1

    block_config = BlockConfiguration.objects.get(
        pk = request.POST['block_config'] )

    pos = BlockInstancePosition(region = region,
                                sortorder = sortorder,
                                block_configuration = block_config)
    pos.save()
    #print "sortorder: %d" % sortorder

    return HttpResponseRedirect( '/' )


def sortblocks(request, group):
    if request.method != 'POST' or not request.user.is_authenticated:
        raise Exception

    # Now resort it ..
    print str(request.POST);
    #return HttpResponse('')
    for blockregion in request.POST.getlist('block_region'):
        sortorder = request.POST[blockregion]
        print "sortorder for %s: %s" % (blockregion, str(sortorder))


        region = get_or_create_region(get_current_group(),
                                      request.user,
                                      blockregion)

        block_instances = BlockInstancePosition.objects.filter(region = region,)
        block_instances.delete()

        if not sortorder:
            continue

        idorder = [e.split('=')[1] for e in sortorder.split('&')]

        pos=1
        for id in idorder:
            # TODO add permission checking ?
            block_config = BlockConfiguration.objects.get( pk = id )
            BlockInstancePosition(region = region,
                                  block_configuration = block_config,
                                  sortorder = pos).save()
            pos+=1

    return HttpResponse('')

    blockregion = request.POST['block_region']
    sortorder = request.POST['sortorder']
    idorder = [e.split('=')[1] for e in sortorder.split('&')]
    region = get_or_create_region(get_current_group(),
                                  request.user,
                                  blockregion)

    block_instances = BlockInstancePosition.objects.filter(region = region,)
    block_instances.delete()

    pos=1
    for id in idorder:
        # TODO add permission checking ?
        block_config = BlockConfiguration.objects.get( pk = id )
        BlockInstancePosition(region = region,
                              block_configuration = block_config,
                              sortorder = pos).save()
        pos+=1
    return HttpResponse( 'Sorted all blocks.' )

