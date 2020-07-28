# encoding: utf-8

import ckan.plugins as p

def datacard_auth(context, data_dict, privilege='package_update'):
    if 'id' not in data_dict:
        data_dict['id'] = data_dict.get('package_id')

    user = context.get('user')

    authorized = p.toolkit.check_access(privilege, context, data_dict)
    if not authorized:
        return {
            'success': False,
            'msg': p.toolkit._(
                'User {0} not authorized to update resource {1}'
                    .format(str(user), data_dict['id'])
            )
        }
    else:
        return {'success': True}

def get_datacard(context, data_dict=None):
    return datacard_auth(context, data_dict, 'package_show')

def search_datacard(context, data_dict=None):
    return datacard_auth(context, data_dict, 'package_search')

def compute_datacard(context, data_dict=None):
    return datacard_auth(context, data_dict)

