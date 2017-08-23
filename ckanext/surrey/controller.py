from logging import getLogger
import urlparse

import requests

import ckan.logic as logic
import ckan.lib.base as base
from ckan.common import _, request, c
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.logic.schema as schema
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.lib.mailer as mailer
from pylons import config
import ckan.lib.captcha as captcha


import ckan.model as model
from urllib import urlencode
from ckan.controllers.package import PackageController
from ckan.logic import get_action, NotFound, NotAuthorized
from ckanext.surrey.util.util import record_is_viewable, resource_is_viewable
#

DataError = dictization_functions.DataError
unflatten = dictization_functions.unflatten


log = getLogger(__name__)
render = base.render
abort = base.abort
redirect = base.redirect


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
        return base.render('package/request_access.html', extra_vars={'package': id, 'package_name': c.pkg_dict['title']})

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

            #return base.render('suggest/form.html')
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
            error_summary['email'] =  u'Missing value'

        if (data_dict["name"] == ''):

            errors['name'] = [u'Missing Value']
            error_summary['name'] =  u'Missing value'


        if (data_dict["suggestion"] == ''):

            errors['suggestion'] = [u'Missing Value']
            error_summary['suggestion'] =  u'Missing value'


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
            #return base.render('suggest/form.html')
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
            error_summary['email'] =  u'Missing value'

        if (data_dict["name"] == ''):

            errors['name'] = [u'Missing Value']
            error_summary['name'] =  u'Missing value'


        if (data_dict["content"] == ''):

            errors['content'] = [u'Missing Value']
            error_summary['content'] =  u'Missing value'


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
    

