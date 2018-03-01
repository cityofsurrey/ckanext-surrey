import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import time

from ckanext.surrey.util.util import get_orgs_user_can_edit, record_is_viewable, resource_is_viewable, most_recent_resource_update, check_if_whitelisted
from ckan.lib.navl.validators import not_empty
from ckan.common import _, request, c, response, g
import ckan.logic as logic
import ckan.lib.base as base
from logging import getLogger
log = getLogger(__name__)


NotAuthorized = logic.NotAuthorized
NotFound = logic.NotFound

# Our custom template helper function.
def format_date(date):
    '''Take timestamp and return a formatted date Month, day Year.'''
    try:
        mytime = time.strptime(date[:10], "%Y-%m-%d")
    except:
        return None
    output = time.strftime("%B %d, %Y", mytime)
    # Just return some example text.
    return output

def update_frequency():
    frequency_list = (u"Yearly", u"Monthly", u"Weekly", u"Daily", u"Realtime", u"Punctual", u"Variable", u"Never")
    return frequency_list

def city_departments():
    department_list = (
        u"City Manager", u"Engineering", u"Finance & Technology", u"Human Resources",
        u"Parks, Recreation & Culture", u"Planning & Development", u"RCMP Support Services",
        u"Surrey Fire Service"
    )
    return department_list

def get_group_list():
    groups = tk.get_action('group_list')(
        data_dict={'all_fields': True})

    return groups

def get_summary_list(num_packages):
    list_without_summary = \
    tk.get_action('package_search')(data_dict={'rows': num_packages, 'sort': 'metadata_modified desc'})['results']
    list_with_summary = []
    for package in list_without_summary:
        list_with_summary.append(tk.get_action('package_show')(
            data_dict={'id': package['name'], 'include_tracking': True})
        )
    return list_with_summary

def get_visit_summary_list(num_packages):
    list_without_summary = tk.get_action('package_search')(data_dict={'rows':num_packages,'sort':'views_recent desc'})['results']
    list_with_summary = []
    for package in list_without_summary:
        list_with_summary.append(tk.get_action('package_show')(
        data_dict={'id':package['name'],'include_tracking':True})
        )
    return list_with_summary

class SurreyFacetPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IFacets, inherit=True)

    def dataset_facets(self, facets_dict, package_type):
        default_facet_titles = {
            'groups': tk._('Categories'),
            'tags': tk._('Tags'),
            'res_format': tk._('Formats')
            # 'license_id': tk._('License'),
        }
        return default_facet_titles

    def group_facets(self, facets_dict, group_type, package_type):
        default_facet_titles = {
            'groups': tk._('Categories'),
            'tags': tk._('Tags'),
            'res_format': tk._('Formats')
            # 'license_id': tk._('License'),
        }
        return default_facet_titles


class SurreyExtraPagesPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)

    def update_config(self, config):
        config['ckan.resource_proxy_enabled'] = True

    def before_map(self, m):
        m.connect('suggest', '/suggest',
                  controller='ckanext.surrey.controller:SuggestController',
                  action='suggest_form')

        m.connect('contact', '/contact',
                  controller='ckanext.surrey.controller:ContactController',
                  action='contact_form')

        m.connect('follow', '/follow',
                  controller='ckanext.surrey.controller:FollowController',
                  action='follow')

        return m


class SurreyTemplatePlugin(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    '''An example that shows how to use the ITemplateHelpers plugin interface.

    '''
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=False)


    num_times_new_template_called = 0
    num_times_read_template_called = 0
    num_times_edit_template_called = 0
    num_times_search_template_called = 0
    num_times_history_template_called = 0
    num_times_package_form_called = 0
    num_times_check_data_dict_called = 0
    num_times_setup_template_variables_called = 0

    # Update CKAN's config settings, see the IConfigurer plugin interface.
    def update_config(self, config):
        # Tell CKAN to use the template files in
        # ckanext/example_itemplatehelpers/templates.
        plugins.toolkit.add_template_directory(config, 'templates')
        plugins.toolkit.add_public_directory(config, 'public')
        plugins.toolkit.add_resource('fanstatic_library', 'ckanext-surrey')


    # Rather than have the IP white list require a full server reboot, we will
    # add a configuration option to make it editable by an admin

    def update_config_schema(self, schema):
        ignore_missing = tk.get_validator('ignore_missing')
        schema.update({
            'ckanext.surrey_whitelist': [ignore_missing]
        })
        return schema

    # Tell CKAN what custom template helper functions this plugin provides,
    # see the ITemplateHelpers plugin interface.
    def get_helpers(self):
        return {
            'format_date': format_date,
            'update_frequency': update_frequency,
            'city_departments': city_departments,
            'get_group_list': get_group_list,
            'get_summary_list': get_summary_list,
			'get_visit_summary_list': get_visit_summary_list,
            'record_is_viewable': record_is_viewable,
            'resource_is_viewable': resource_is_viewable,
            'most_recent_resource_update': most_recent_resource_update,
        }

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):
        schema.update({
            'update_frequency': [tk.get_validator('ignore_missing'),
                                 tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'coordinate_system': [tk.get_validator('ignore_missing'),
                                  tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'more_information': [tk.get_validator('ignore_missing'),
                                 tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'attribute_details': [tk.get_validator('ignore_missing'),
                                  tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'is_geospatial': [tk.get_validator('ignore_missing'),
                              tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'purpose': [tk.get_validator('ignore_missing'),
                        tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'data_quality': [tk.get_validator('ignore_missing'),
                        tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'lineage': [tk.get_validator('ignore_missing'),
                        tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'department': [tk.get_validator('ignore_missing'),
                        tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'view_audience': [not_empty, tk.get_converter('convert_to_extras')],
            'metadata_visibility': [not_empty, tk.get_converter('convert_to_extras')]
        })

        schema.update({
            'custodian': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
            'custodian_email': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]
        })

        return schema

    def create_package_schema(self):
        schema = super(SurreyTemplatePlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(SurreyTemplatePlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(SurreyTemplatePlugin, self).show_package_schema()

        # Add our custom_text field to the dataset schema.
        schema.update({
            'update_frequency': [tk.get_converter('convert_from_extras'),
                                 tk.get_validator('ignore_missing')]
        })

        schema.update({
            'coordinate_system': [tk.get_converter('convert_from_extras'),
                                  tk.get_validator('ignore_missing')]
        })

        schema.update({
            'more_information': [tk.get_converter('convert_from_extras'),
                                 tk.get_validator('ignore_missing')]
        })

        schema.update({
            'attribute_details': [tk.get_converter('convert_from_extras'),
                                  tk.get_validator('ignore_missing')]
        })

        schema.update({
            'is_geospatial': [tk.get_converter('convert_from_extras'),
                              tk.get_validator('ignore_missing')]
        })

        schema.update({
            'purpose': [tk.get_converter('convert_from_extras'),
                        tk.get_validator('ignore_missing')]
        })

        schema.update({
            'data_quality': [tk.get_converter('convert_from_extras'),
                        tk.get_validator('ignore_missing')]
        })

        schema.update({
            'lineage': [tk.get_converter('convert_from_extras'),
                        tk.get_validator('ignore_missing')]
        })

        schema.update({
            'department': [tk.get_converter('convert_from_extras'),
                        tk.get_validator('ignore_missing')]
        })

        schema.update({
            'view_audience': [tk.get_converter('convert_from_extras'), not_empty],
            'metadata_visibility': [tk.get_converter('convert_from_extras'), not_empty]
        })

        schema.update({
            'custodian':[tk.get_converter('convert_from_extras'),
                        tk.get_validator('ignore_missing')],
            'custodian_email':  [tk.get_converter('convert_from_extras'),
                        tk.get_validator('ignore_missing')]
        })

        return schema

    # These methods just record how many times they're called, for testing
    # purposes.
    # TODO: It might be better to test that custom templates returned by
    # these methods are actually used, not just that the methods get
    # called.

    def setup_template_variables(self, context, data_dict):
        SurreyTemplatePlugin.num_times_setup_template_variables_called += 1
        return super(SurreyTemplatePlugin, self).setup_template_variables(
            context, data_dict)

    def new_template(self):
        SurreyTemplatePlugin.num_times_new_template_called += 1
        return super(SurreyTemplatePlugin, self).new_template()

    def read_template(self):
        SurreyTemplatePlugin.num_times_read_template_called += 1
        return super(SurreyTemplatePlugin, self).read_template()

    def edit_template(self):
        SurreyTemplatePlugin.num_times_edit_template_called += 1
        return super(SurreyTemplatePlugin, self).edit_template()

    def search_template(self):
        SurreyTemplatePlugin.num_times_search_template_called += 1
        return super(SurreyTemplatePlugin, self).search_template()

    def history_template(self):
        SurreyTemplatePlugin.num_times_history_template_called += 1
        return super(SurreyTemplatePlugin, self).history_template()

    def package_form(self):
        SurreyTemplatePlugin.num_times_package_form_called += 1
        return super(SurreyTemplatePlugin, self).package_form()

    # check_data_dict() is deprecated, this method is only here to test that
    # legacy support for the deprecated method works.
    def check_data_dict(self, data_dict, schema=None):
        SurreyTemplatePlugin.num_times_check_data_dict_called += 1

    def before_map(self, map):
        from routes.mapper import SubMapper

        package_controller = 'ckanext.surrey.controller:SurreyPackageController'
        api_controller = 'ckanext.surrey.controller:SurreyAPIController'

        GET = dict(method=['GET'])
        map.connect('home', '/', controller='home', action='index')

        with SubMapper(map, controller=package_controller, path_prefix='/dataset') as m:
            m.connect('search', '/', action='search', highlight_actions='index search')
            m.connect('add dataset', '/new', action='new')
            m.connect('request access', '/{id}/access', action='request_access')
            m.connect('download resource', '/{id}/resource/{resource_id}/download/{filename}', action='resource_download')
            m.connect('/{id}/resource/{resource_id}', action='resource_read')
            m.connect('dataset read', '/{id}', action='read', ckan_icon='sitemap')
            m.connect('resources', '/resources/{id}', action='resources')


        with SubMapper(map, controller=api_controller, path_prefix='/api{ver:/1|/2|/3|}', ver='/3') as m:
            m.connect('/action/package_list', action='restricted_package_list', conditions=GET)
            m.connect('/action/current_package_list_with_resources', action='restricted_package_list_with_resources', conditions=GET)
            m.connect('/action/package_show', action='restricted_package_show', conditions=GET)
        return map

    def after_map(self, map):
        return map

    def before_search(self, search_params):
        '''
        Customizes package search and applies filters based on the dataset metadata-visibility
        and user roles.
        '''

        # Change the default sort order when no query passed
        if not search_params.get('q') and search_params.get('sort') in (None, 'rank'):
            search_params['sort'] = 'record_publish_date desc, metadata_modified desc'

        # Change the query filter depending on the user

        if 'fq' in search_params:
            fq = search_params['fq']

        else:
            fq = ''

        if 'facet.field' in search_params:
            ff = search_params['facet.field']
        # need to append solr param q.op to force an AND query
        if 'q' in search_params:
            q = search_params['q']
            if q != '':
                q = '{!lucene q.op=AND}' + q
                search_params['q'] = q

        try:
            user_name = c.user or 'visitor'
	    white_listed = check_if_whitelisted(c.remote_addr)

            #  There are no restrictions for sysadmin
            if (c.userobj and c.userobj.sysadmin == True) or white_listed:
                fq += ' '
            else:
                fq += ' -metadata_visibility:("Private")'
                #if user_name != 'visitor':
                #    fq += ' +('
                #    if 'owner_org' not in fq:

                #        user_id = c.userobj.id
                #        # Get the list of orgs that the user is an admin or editor of
                #        user_orgs = get_orgs_user_can_edit(c.userobj)
                #        if user_orgs != []:
                #            fq += ' OR ' + 'owner_org:(' + ' OR '.join(user_orgs) + ')'

                #        fq += ')'
                ## Public user can only view public and published records
                ## All need to check for the absence of the metadata_visibility field to handle legacy datasets
                #else:
                #    fq += ' -metadata_visibility:("Private")'

        except Exception:
            if 'fq' in search_params:
                fq = search_params['fq']
            else:
                fq = ''
            fq += ' -metadata_visibility:("Private")'

        search_params['fq'] = fq
        return search_params

    def after_search(self, search_results, search_params):
        return search_results

    def before_view(self, pkg_dict):
        if check_if_whitelisted(c.remote_addr): # Whitelist set via CKAN admin config panel
            return pkg_dict

        if not record_is_viewable(pkg_dict, c.userobj):
            base.abort(401, _('Unauthorized to read package %s') % pkg_dict.get("title"))

        return pkg_dict

    def before_index(self, pkg_dict):
        '''
        Makes the sort by name case insensitive.
        Note that the search index must be rebuild for the first time in order for the changes to take affect.
        '''
        title = pkg_dict['title']
        if title:
            # Assign title to title_string with all characters switched to lower case.
            pkg_dict['title_string'] = title.lower()

        return pkg_dict
