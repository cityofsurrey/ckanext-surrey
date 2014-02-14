from logging import getLogger
import urlparse

import requests

import ckan.logic as logic
import ckan.lib.base as base
from ckan.common import _, request, c

log = getLogger(__name__)


class SuggestController(base.BaseController):

    def __before__(self, action, **env):
        base.BaseController.__before__(self, action, **env)
        try:
            context = {'model': base.model, 'user': base.c.user or base.c.author,
                       'auth_user_obj': base.c.userobj}
            logic.check_access('site_read', context)
        except logic.NotAuthorized:
            base.abort(401, _('Not authorized to see this page'))


    def suggest_form(self):
        data_dict = {'resource_id': 'r123'}

        context = {'model': base.model, 'session': base.model.Session,
                   'user': base.c.user or base.c.author,
                   'for_view': True}

        return base.render('suggest/form.html')