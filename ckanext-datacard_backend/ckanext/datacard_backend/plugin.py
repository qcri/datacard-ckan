import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.datacard_backend.logic.action as action
import ckanext.datacard_backend.logic.auth as auth

class DatacardBackendPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'datacard_backend')

    # IActions

    def get_actions(self):
        return {'get_datacard': action.get_datacard,
                'compute_datacard': action.compute_datacard,
                'search_datacard': action.search_datacard
        }

    # IAuthFunctions

    def get_auth_functions(self):
        return {'get_datacard': auth.get_datacard,
                'compute_datacard': auth.compute_datacard,
                'search_datacard': auth.search_datacard
        }
