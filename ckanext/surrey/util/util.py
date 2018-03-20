import re

from logging import getLogger
import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.common import c
import pylons.config as config
from ckan.lib.base import _


log = getLogger(__name__)


def get_whitelist_settings():
    white_list = config.get('ckanext.surrey_whitelist', '')
    if white_list:
        delimiters = [' , ', ', ', ' ,', ',', '  ', ' ', ' ; ', ' ;', '; ', ';', ' | ', ' |', '| ', '|']
        for ch in delimiters:
            white_list = white_list.replace(ch, ',')
        return white_list.split(',')
    return white_list


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


def get_package_metadata_visibility(pkg):
    mv = None
    try:
        mv = pkg['metadata_visibility']
    except KeyError:
        try:
            pkg_extras = pkg.extras
        except AttributeError:
            try:
                pkg_extras = pkg['extras']
            except KeyError:
                return mv
        try:
            for extras in pkg_extras:
                if 'key' in extras:
                    if extras['key'] == 'metadata_visibility':
                        mv = extras['value']
        except Exception as e:
            log.error('Except: %s' % (e,))
    return mv


def get_view_audience(pkg):
    mv = None
    try:
        mv = pkg['view_audience']
    except KeyError:
        try:
            pkg_extras = pkg.extras
        except AttributeError:
            try:
                pkg_extras = pkg['extras']
            except KeyError:
                return mv
        try:
            for extras in pkg_extras:
                if 'key' in extras:
                    if extras['key'] == 'view_audience':
                        mv = extras['value']
        except Exception as e:
            log.error('Except: %s' % (e,))
    return mv


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



def most_recent_resource_update(pkg_dict):
    return max([r['last_modified'] for r in pkg_dict['resources']])
