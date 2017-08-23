
from logging import getLogger
import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.common import  c
from ckan.lib.base import _

log = getLogger(__name__)

def get_package_extras_by_key(pkg_extra_key, pkg_dict):
    '''
    Gets the specified `extras` field by pkg_extra_key, if it exists
    Returns False otherwise
    '''
    if 'extras' in pkg_dict:
        try:
            pkg_extras = pkg_dict.extras
        except AttributeError:
            pkg_extras = pkg_dict['extras']
        for extras in pkg_extras:
            if 'key' in extras:
                if extras['key'] == pkg_extra_key:
                    return extras['value']
        return False
    else:
        return False


# def get_package_metadata_visibility(pkg):
#     mv = None
#     try:
#         pkg_extras = pkg.extras
#     except AttributeError:
#         try:
#             pkg_extras = pkg['extras']
#         except KeyError:
#             return mv
#     try:
#         for extras in pkg_extras:
#             if 'key' in extras:
#                 if extras['key'] == 'metadata_visibility':
#                     mv = extras['value']
#     except Exception as e:
#         log.info('Except: %s' % (e,))
#     return mv

def get_package_owner_org(pkg):
    try:
        oo = pkg.owner_org
    except Exception as e:
        log.info('Exception %s' % (e))
        return False
    return oo

def get_username(id):
    '''
    Returns the user name for the given id.
    '''

    try:
        user = toolkit.get_action('user_show')(data_dict={'id': id})
        return user['name']
    except toolkit.ObjectNotFound:
        return None


def get_orgs_user_can_edit(userobj):
    '''
    Returns the list of id's of organizations that the current logged in user
    can edit. The user must have an admin or editor role in the organization.
    '''

    if not userobj:
        return []


    '''
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}
    perm_dict = {'permission' : 'create_dataset'}
    orgs = toolkit.get_action('organization_list_for_user')(data_dict=perm_dict)
    orgs = [org['id'] for org in orgs]

    '''
    orgs = userobj.get_group_ids('organization', 'editor') + c.userobj.get_group_ids('organization', 'admin')
    return orgs


def get_user_orgs(user_id, role=None):
    '''
    Returns the list of orgs and suborgs that the given user belongs to and has the given role('admin', 'member', 'editor', ...)
    '''

    member_query = model.Session.query(model.Member.group_id.label('id')) \
        .filter(model.Member.table_name == 'user') \
        .filter(model.Member.state == 'active') \
        .filter(model.Member.table_id == user_id) \
        .filter(model.Member.capacity == role)


    org_ids = member_query.distinct()

    orgs_dict = [org.__dict__ for org in org_ids.all()]

    return orgs_dict



def record_is_viewable(pkg_dict, userobj):
    '''
    Checks if the user is authorized to view the dataset.
    Public users can only see published or pending archive records and only if the metadata-visibility is public.
    Government users who are not admins or editors can only see the published or pending  archive records.
    Editors and admins can see all the records of their organizations in addition to what government users can see.
    '''
    log.info('Checking if %s is viewable' % pkg_dict)

    # Sysadmin can view all records
    if userobj and userobj.sysadmin == True :
        return True

    if 'metadata_visibility' in pkg_dict:
        metadata_visibility = pkg_dict['metadata_visibility']
    else:
        metadata_visibility = get_package_extras_by_key('metadata_visibility', pkg_dict)


    log.info('Metadata Visibility set to %s' % (metadata_visibility))
    if userobj:
        log.info('Current user is %s' % (userobj.name))

    if metadata_visibility == 'Public' :
        return True
    
    # We might have legacy datasets that do not contain the metadata_visibility field. 
    if metadata_visibility is None:
        return True

    if 'owner_org' in pkg_dict:
        owner_org = pkg_dict['owner_org']
    else:
        owner_org = get_package_extras_by_key('owner_org', pkg_dict)

    if userobj:
        user_orgs = get_orgs_user_can_edit(userobj)

        if owner_org in user_orgs:
            return True
    
    log.info('No authorized user found.')
    return False


def resource_is_viewable(pkg_dict, userobj):
    log.info('Checking if %s is viewable' % pkg_dict['name'])

    if record_is_viewable(pkg_dict, userobj) == False:
        return False

    # Sysadmin can view all records
    if userobj and userobj.sysadmin == True:
        return True

    if 'view_audience' in pkg_dict:
        view_audience = pkg_dict['view_audience']
    else:
        view_audience = get_package_extras_by_key('view_audience', pkg_dict)

    log.info('view_audience set to %s' % (view_audience))
    if userobj:
        log.info('Current user is %s' % (userobj.name))

    if view_audience == 'Public':
        return True

    # We might have legacy datasets that do not contain the metadata_visibility field.
    if view_audience is None:
        return True

    if 'owner_org' in pkg_dict:
        owner_org = pkg_dict['owner_org']
    else:
        owner_org = get_package_extras_by_key('owner_org', pkg_dict)

    if userobj:
        user_orgs = get_orgs_user_can_edit(userobj)

        if owner_org in user_orgs:
            return True

    log.info('No authorized user found.')
    return False