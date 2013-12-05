import ckan.plugins as plugins
import time

# Our custom template helper function.
def format_date(date):
    '''Take timestamp and return a formatted date Month, day Year.'''
    mytime = time.strptime(date[:10], "%Y-%m-%d")
    output = time.strftime("%B %d, %Y", mytime) 
    # Just return some example text.
    return output 

class SurreyTemplatePlugin(plugins.SingletonPlugin):
    '''An example that shows how to use the ITemplateHelpers plugin interface.

    '''
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # Update CKAN's config settings, see the IConfigurer plugin interface.
    def update_config(self, config):

        # Tell CKAN to use the template files in
        # ckanext/example_itemplatehelpers/templates.
        plugins.toolkit.add_template_directory(config, 'templates')

    # Tell CKAN what custom template helper functions this plugin provides,
    # see the ITemplateHelpers plugin interface.
    def get_helpers(self):
        return {'format_date': format_date}
