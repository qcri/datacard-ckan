# encoding: utf-8

import ckan.logic as logic
import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckanext.datacard_backend.generators.mlgenerator import MLDatacardGenerator

'''
 Parameters must contain one of 'id' or 'name'
'''
@logic.side_effect_free
def get_datacard(context, data_dict):
    pkg_dict = tk.get_action('package_show')(context, data_dict)
    extras = pkg_dict['extras']
    grouped = {}
    for extra in extras:
        if extra['key'].startswith('datacard'):
            tokens = extra['key'].split('_')
            group_id = tokens[1]
            metric_id = tokens[2]
            metric_value = extra['value']
            if group_id not in grouped:
                grouped[group_id] = {}
            grouped[group_id][metric_id] = metric_value
    print('-- grouped datacard: ', grouped)
    return grouped

'''
 Parameters must contain 'key' and 'value'
'''
@logic.side_effect_free
def search_datacard(context, data_dict):
    '''
    Key should be of format <group>_<metric>
    '''
    key = data_dict['key']
    value = data_dict['value']
    if key is None or key == '':
        return {'success': False, 'msg': 'Please provide a search key'}
    if value is None or value == '':
        return {'success': False, 'msg': 'Please provide a search value'}
    
    dckey = 'datacard_' + key
    new_data_dict={'q': dckey + ':' + str(value)}
    print('Searching for: ', new_data_dict)
    search_results = tk.get_action('package_search')(context, new_data_dict)
    print('Got result: ', search_results)
    return search_results

'''
 Parameters must contain one of 'id' or 'name'
'''
@logic.side_effect_free
def compute_datacard(context, data_dict):
    # Check existence of dataset
    pkg_dict = tk.get_action('package_show')(context, data_dict)
    if pkg_dict is None or 'id' not in pkg_dict:
        return pkg_dict
    pkg_id = pkg_dict['id']
    print('Generating datacard for ', pkg_id)
    # Invoke each generator in a separate background job
    generator = MLDatacardGenerator(pkg_id)
    job = tk.enqueue_job(generator.generate, queue=tk._('datacard'))
    return {'success': True, 'msg': 'Datacard creation has started in background'}

