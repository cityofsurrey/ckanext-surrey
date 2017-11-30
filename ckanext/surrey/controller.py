import os
from logging import getLogger

import ckan.lib.base as base
from ckan.common import _, request, c
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.model as model
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.lib.mailer as mailer
from pylons import config
import ckan.lib.captcha as captcha

from urllib import urlencode
from ckan.controllers.package import PackageController
from ckan.controllers.api import ApiController

from ckanext.surrey.util.util import record_is_viewable, resource_is_viewable, check_if_whitelisted

DataError = dictization_functions.DataError
unflatten = dictization_functions.unflatten

log = getLogger(__name__)
render = base.render
abort = base.abort
redirect = base.redirect
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError

# By default package_list returns only the last 10 modified records
default_limit = 100000000
default_offset = 0

CONTENT_TYPES = {
    'text': 'text/plain;charset=utf-8',
    'html': 'text/html;charset=utf-8',
    'json': 'application/json;charset=utf-8',
}


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


class SurreyPackageController(PackageController):
    def index(self):
        url = h.url_for(controller='package', action='search')
        log.info('Request url: %s' % (url,))
        params = [(k, v) for k, v in request.params.items()]
        log.info(params)
        if not c.user:
            params.append(('metadata_visibility', 'Public'))
            redirect(url_with_params(url, params))
        else:
            redirect(url_with_params(url, params))

    def read(self, id):
        '''
                First calls ckan's default read to get package data.
                Then it checks if the package can be viewed by the user
                '''
        # the ofi object is now in the global vars for this view, to use it in templates, call `c.ofi`
        result = super(SurreyPackageController, self).read(id)

        log.debug('Called read method')
        # Check if user can view this record
        if not record_is_viewable(c.pkg_dict, c.userobj):
            base.abort(401, _('Unauthorized to read package %s') % id)
        return result

    def resource_read(self, id, resource_id):
        '''
        First calls ckan's default resource read to get the resource and package data.
        Then it checks if the resource can be viewed by the user
        '''

        result = super(SurreyPackageController, self).resource_read(id, resource_id)
        log.debug('Called resource_read method')
        if not record_is_viewable(c.pkg_dict, c.userobj):
            base.abort(401, _('Unauthorized to read package %s') % id)
        if not resource_is_viewable(c.pkg_dict, c.userobj):
            base.abort(401, _('Unauthorized to read resource %s') % c.pkg_dict['name'])
        return result

    def request_access(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        try:
            pkg = get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('Resource not found'))
        return base.render('package/request_access.html', extra_vars={'package': id, 'package_name': pkg['title']})

    def resource_download(self, id, resource_id, filename=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        try:
            pkg = get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('Resource not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read resource %s') % id)

        if not record_is_viewable(pkg, c.userobj):
            base.abort(401, _('Unauthorized to read package %s') % id)
        if not resource_is_viewable(pkg, c.userobj):
            base.abort(401, _('Unauthorized to read resource %s') % pkg['name'])
        result = super(SurreyPackageController, self).resource_download(id, resource_id, filename)
        return result


class SurreyAPIController(ApiController):
    def restricted_package_list(self):
        '''
        Returns a list of site packages depending on the user.
        The public users could only see published public records.
        Each user can only see private records of his/her own organization
        '''
        # FIXME: override with IActions plugin instead
        from ckan.lib.search import SearchError
        log.info('Calling restricted_package_list method')

        help_str = "Return a list of the names of the site's datasets (packages).\n\n    " + \
                   ":param limit: if given, the list of datasets will be broken into pages of\n" + \
                   "        at most ``limit`` datasets per page and only one page will be returned\n" + \
                   "        at a time (optional)\n    :type limit: int\n    :param offset: when ``limit`` " + \
                   "is given, the offset to start returning packages from\n    :type offset: int\n\n" + \
                   "    :rtype: list of strings\n\n    "

        return_dict = {"help": help_str}

        # Get request parameters (number of records to be returned and the starting package)
        try:
            limit = int(request.params.get('limit', default_limit))
        except ValueError:
            limit = default_limit
        try:
            offset = int(request.params.get('offset', default_offset))
        except ValueError:
            offset = 0

        try:
            data_dict = {
                'q': '',
                'fq': '',
                'start': offset,
                'rows': limit,
                'sort': 'views_total desc'
            }
            # Use package_search to filter the list
            context = {'model': model, 'session': model.Session, 'user': c.user, 'auth_user_obj': c.userobj}
            query = get_action('package_search')(context, data_dict)
        except SearchError as se:
            return self._finish_bad_request()

        result = []
        for pkg in query['results']:
            result.append(pkg['name'])

        return_dict['success'] = True
        return_dict['result'] = result
        return self._finish_ok(return_dict)

    def restricted_package_list_with_resources(self):
        '''
        Returns a list of site packages depending on the user.
        The public users could only see published public records.
        Each user can only see private records of his/her own organization
        '''
        # FIXME: override with IActions plugin instead
        from ckan.lib.search import SearchError

        help_str = "Returns a list of the names of top 10 most viewed datasets (packages).\n\n    " + \
                   ":param limit: if given, the list of datasets will be broken into pages of\n" + \
                   "        at most ``limit`` datasets per page and only one page will be returned\n" + \
                   "        at a time (optional)\n    :type limit: int\n    :param offset: when ``limit`` " + \
                   "is given, the offset to start\n        returning packages from\n    :type offset: int\n\n" + \
                   "    :rtype: list of strings\n\n    "

        return_dict = {"help": help_str}

        # Get request parameters (number of records to be returned and the starting package)
        try:
            limit = int(request.params.get('limit', default_limit))
        except ValueError:
            limit = default_limit

        try:
            offset = int(request.params.get('offset', default_offset))
        except ValueError:
            offset = 0

        try:
            data_dict = {
                'q': '',
                'fq': '',
                'start': offset,
                'rows': limit,
                'sort': 'views_total desc'
            }

            # Use package_search to filter the list
            context = {'model': model, 'session': model.Session, 'user': c.user, 'auth_user_obj': c.userobj}
            query = get_action('package_search')(context, data_dict)
        except SearchError as se:
            print 'Search error', str(se)
            return self._finish_bad_request()

        return_dict['success'] = True
        return_dict['result'] = query['results']
        return self._finish_ok(return_dict)

    def restricted_package_show(self):
        '''
        Returns record's data with the given id only if the user is allowed to view the record.
        '''
        # FIXME: use IAuth plugin for authorization check and
        # use IPackageController to fill in extra values
        # then remove this method

        help_str = "Shows the package info with the given id. Param : id"
        pkg_id = request.params.get('id', '')
        return_dict = {"help": help_str}
        try:
            context = {'model': model, 'session': model.Session, 'user': c.user, 'auth_user_obj': c.userobj}
            pkg = get_action('package_show')(context, {'id': pkg_id})

            from ckanext.surrey.util.util import record_is_viewable, resource_is_viewable

            if not record_is_viewable(pkg, c.userobj):
                return_dict['success'] = False
                return_dict['error'] = {'__type': 'Authorization Error', 'message': _('Access denied')}
                return self._finish(403, return_dict, content_type='json')
            if not resource_is_viewable(pkg, c.userobj):
                pkg['resources'] = None
                return_dict[
                    'msg'] = "Access to these resources are restricted. Please submit an FOI request via http://www.surrey.ca/city-government/3062.aspx or contact opendata@surrey.ca."
            return_dict['success'] = True
            return_dict['result'] = pkg
        except NotFound as e:
            return_dict['error'] = {'__type': 'Not Found Error',
                                    'message': _('Not found')}
            if hasattr(e, 'extra_msg'):
                return_dict['error']['message'] += ': %s' % e.extra_msg
            return_dict['success'] = False
            return self._finish(404, return_dict, content_type='json')
        except ValidationError as e:
            error_dict = e.error_dict
            error_dict['__type'] = 'Validation Error'
            return_dict['error'] = error_dict
            return_dict['success'] = False
            # CS nasty_string ignore
            log.error('Validation error: %r' % str(e.error_dict))
            return self._finish(200, return_dict, content_type='json')

        return self._finish_ok(return_dict)


class FollowController(base.BaseController):
    def __before__(self, action, **env):
        base.BaseController.__before__(self, action, **env)
        try:
            context = {'model': base.model, 'user': base.c.user or base.c.author,
                       'auth_user_obj': base.c.userobj}
            logic.check_access('site_read', context)
        except logic.NotAuthorized:
            base.abort(401, _('Not authorized to see this page'))

    def follow(self):

        return base.render('follow/read.html')


class SuggestController(base.BaseController):
    def __before__(self, action, **env):
        base.BaseController.__before__(self, action, **env)
        try:
            context = {'model': base.model, 'user': base.c.user or base.c.author,
                       'auth_user_obj': base.c.userobj}
            logic.check_access('site_read', context)
        except logic.NotAuthorized:
            base.abort(401, _('Not authorized to see this page'))

    def _send_suggestion(self, context):
        try:
            data_dict = logic.clean_dict(unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')

            c.form = data_dict['name']
            captcha.check_recaptcha(request)

            # return base.render('suggest/form.html')
        except logic.NotAuthorized:
            base.abort(401, _('Not authorized to see this page'))

        except captcha.CaptchaError:
            error_msg = _(u'Bad Captcha. Please try again.')
            h.flash_error(error_msg)
            return self.suggest_form(data_dict)

        errors = {}
        error_summary = {}

        if (data_dict["email"] == ''):
            errors['email'] = [u'Missing Value']
            error_summary['email'] = u'Missing value'

        if (data_dict["name"] == ''):
            errors['name'] = [u'Missing Value']
            error_summary['name'] = u'Missing value'

        if (data_dict["suggestion"] == ''):
            errors['suggestion'] = [u'Missing Value']
            error_summary['suggestion'] = u'Missing value'

        if len(errors) > 0:
            return self.suggest_form(data_dict, errors, error_summary)
        else:
            # #1799 User has managed to register whilst logged in - warn user
            # they are not re-logged in as new user.
            mail_to = config.get('email_to')
            recipient_name = 'CKAN Surrey'
            subject = 'CKAN - Dataset suggestion'

            body = 'Submitted by %s (%s)\n' % (data_dict["name"], data_dict["email"])

            if (data_dict["category"] != ''):
                body += 'Category: %s' % data_dict["category"]

            body += 'Request: %s' % data_dict["suggestion"]

            try:
                mailer.mail_recipient(recipient_name, mail_to,
                                      subject, body)
            except mailer.MailerException:
                raise

            return base.render('suggest/suggest_success.html')

    def suggest_form(self, data=None, errors=None, error_summary=None):
        suggest_new_form = 'suggest/suggest_form.html'

        context = {'model': base.model, 'session': base.model.Session,
                   'user': base.c.user or base.c.author,
                   'save': 'save' in request.params,
                   'for_view': True}

        if (context['save']) and not data:
            return self._send_suggestion(context)

        data = data or {}
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        c.form = base.render(suggest_new_form, extra_vars=vars)

        return base.render('suggest/form.html')


class ContactController(base.BaseController):
    def __before__(self, action, **env):
        base.BaseController.__before__(self, action, **env)
        try:
            context = {'model': base.model, 'user': base.c.user or base.c.author,
                       'auth_user_obj': base.c.userobj}
            logic.check_access('site_read', context)
        except logic.NotAuthorized:
            base.abort(401, _('Not authorized to see this page'))

    def _send_contact(self, context):
        try:
            data_dict = logic.clean_dict(unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')

            c.form = data_dict['name']
            captcha.check_recaptcha(request)
            # return base.render('suggest/form.html')
        except logic.NotAuthorized:
            base.abort(401, _('Not authorized to see this page'))
        except captcha.CaptchaError:
            error_msg = _(u'Bad Captcha. Please try again.')
            h.flash_error(error_msg)
            return self.contact_form(data_dict)

        errors = {}
        error_summary = {}

        if (data_dict["email"] == ''):
            errors['email'] = [u'Missing Value']
            error_summary['email'] = u'Missing value'

        if (data_dict["name"] == ''):
            errors['name'] = [u'Missing Value']
            error_summary['name'] = u'Missing value'

        if (data_dict["content"] == ''):
            errors['content'] = [u'Missing Value']
            error_summary['content'] = u'Missing value'

        if len(errors) > 0:
            return self.suggest_form(data_dict, errors, error_summary)
        else:
            mail_to = config.get('email_to')
            recipient_name = 'CKAN Surrey'
            subject = 'CKAN - Contact/Question from visitor'

            body = 'Submitted by %s (%s)\n' % (data_dict["name"], data_dict["email"])

            body += 'Request: %s' % data_dict["content"]

            try:
                mailer.mail_recipient(recipient_name, mail_to,
                                      subject, body)
            except mailer.MailerException:
                raise

            return base.render('contact/success.html')

    def contact_form(self, data=None, errors=None, error_summary=None):
        suggest_new_form = 'contact/form.html'

        context = {'model': base.model, 'session': base.model.Session,
                   'user': base.c.user or base.c.author,
                   'save': 'save' in request.params,
                   'for_view': True}

        if (context['save']) and not data:
            return self._send_contact(context)

        data = data or {}
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        c.form = base.render(suggest_new_form, extra_vars=vars)

        return base.render('contact/contact_base.html')


