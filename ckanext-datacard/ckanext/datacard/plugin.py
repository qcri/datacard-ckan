import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ast
import pandas as pd

from plots import generate_datacard_plot

def _update_datacard(package_id):
    import json
    import requests
           
    def postrequest(url, data, encode_json=True):
        headers = {'X-CKAN-API-Key': '89a1f7ae-4e6a-4f91-bfd8-001e8925e024'}
        if encode_json:
            data = json.dumps(data).encode('utf8')
            headers['Content-Type']='application/json'
        # Make the HTTP request.
        # request = urllib.request.Request(url, data, headers, method='POST')
        # print('Posting request: ', request.get_full_url())
        try:
            response = requests.post(url, data=data, headers=headers) #urllib.request.urlopen(request)
            response_dict = json.loads(response.content)
            print('*** response: ', response.content)
            assert response_dict['success'] is True

            # package_create returns the created package as its result.
            result = response_dict['result']
            return result
        except requests.exceptions.RequestException as e:
            print(e)
            return None

    # fetch all resource ids and/or urls
    url = 'http://127.0.0.1:5050/api/action/package_show'
    data_dict = {
                'id': package_id
    }
    result = postrequest(url, data_dict, False)
    urls = []
    resourceIds = []
    extras = []
    if result is not None:
        for resource in result['resources']:
            urls.append(resource['url'])
            resourceIds.append(resource['id'])
        extras = list(result['extras'])
        del result['extras'] # no longer needed

    # remove old datacard from extras 
    print('*** Extras fetched: ', extras)
    existingDatacards = []
    for extra in extras:
        if extra['key'].startswith(u'datacard_group'):
            existingDatacards.append(extra)
    for extra in existingDatacards:
        extras.remove(extra)
    print('*** Extras after removal: ', extras)

    # urls = ["http://127.0.0.1:5050/dataset/04087d62-ea7e-448f-8562-203fde1d99ac/resource/623b5201-a61f-42e5-9496-cedf5b18e260/download/jhu-file.csv"]
    # resourceIds = ["623b5201-a61f-42e5-9496-cedf5b18e260"]

    # for each resource download csv dump using resource urls

    # create dummy datacard local to each
    datacard = {}
    sum = 0
    for id in resourceIds:
        datacard[u'datacard_group1_' + id + '_metric'] = 25
        sum += 1

    # create dummy datacard global
    datacard[u'datacard_group1_metric'] = sum
    datacard[u'datacard_group2_stat1'] = sum*sum
    datacard[u'datacard_group2_stat2'] = 1/sum

    # add to extras
    for (k, v) in datacard.items():
        newExtra = {}
        newExtra[u'key'] = k
        newExtra[u'value'] = v
        extras.append(newExtra)
    print('*** Extras after addition: ', extras)
    result['extras'] = extras

    # call api to upload datacard as extras
    url =  'http://127.0.0.1:5050/api/action/package_update'
    data_dict = result
    result = postrequest(url, data_dict)

def fetch_grouped_datacard(pkg_dict):
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
    # print('-- grouped datacard: ', grouped)
    return grouped

# packages is a list of package dicts in unicode
def build_datacard_plot(packages):
    print('-- Received plot request: ')
    # Schema for dataframe for each group: ( package, metric1, metric2, ...)
    groupedDF = {}
    # fetch grouped datacard from each pkg dict
    pkglist = []
    groups = []
    metrics = {}
    for pkg in ast.literal_eval(packages):
        pkgname = pkg['name']
        # print('-- Getting package: ', pkgname)
        metrics[pkgname] = fetch_grouped_datacard(pkg)
        pkglist.append(pkgname)
        groups.extend(metrics[pkgname].keys())

    # merge the data from packages to create a dataframe
    groups = set(groups)
    print('Found groups: ', groups)
    groupedDF = {}
    for group in groups:
        # print('-- Iterating group: ', group)
        recordlist = []
        for pkg in pkglist:
            # print('-- Iterating package: ', pkg)
            if metrics[pkg] is None or len(metrics[pkg]) < 1:
                continue
            if group not in metrics[pkg]:
                continue
            groupData = metrics[pkg][group]
            # print('-- Group data: ', groupData)
            record = {}
            record['package'] = pkg
            for (k, v) in groupData.items():
                record[k] = v
            # print('-- Record data: ', record)
            recordlist.append(record)
    
        print('-- Creating grouped dataframe for ', group, ' : ', recordlist)
        groupedDF[group] = pd.DataFrame(recordlist)

    # build a plot with slider to select a group
    return generate_datacard_plot(groupedDF, groups, html=True)
    # return('<div><a class="btn inspect-datacard">Inspect Datacard</a></div>')

class DatacardPlugin(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceController)
    plugins.implements(plugins.IDatasetForm)
    # plugins.implements(plugins.IPackageController)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.ITemplateHelpers)

    def _get_datacard_key(self):
        return tk.config.get(
            'ckan.datacard.datacard_key', 'datacard')
    
    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic', 'datacard')

    # IDatasetForm

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):
        schema.update({ self._get_datacard_key() :
                        [tk.get_validator('ignore_missing'),
                         tk.get_converter('convert_to_extras')]
        })
        print('--Modifying package schema')
        return schema
    
    def create_package_schema(self):
        schema = super(DatacardPlugin, self).create_package_schema()
        # schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(DatacardPlugin, self).update_package_schema()
        # schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(DatacardPlugin, self).show_package_schema()
        #schema.update({ self._get_datacard_key() :
        #                [tk.get_converter('convert_from_extras'),
        #                 tk.get_validator('ignore_missing')]
        #})
        print('--Converted from extras schema: ', schema['__extras'])
        return schema

    def setup_template_variables(self, context, data_dict):
        return super(DatacardPlugin, self).setup_template_variables(
                context, data_dict)

    # IResourceController
  
    def _after_create_or_update(self, context, resource):        
        url = resource['url']
        print('--Modified resource at ', {url}, ' from package ', context['package'])
        # start a background job to prepare datacard
        job = tk.enqueue_job(_update_datacard, args=(resource['package_id'],), queue=tk._('datacard'))

    def before_create(self, context, resource):
        pass

    def after_create(self, context, resource):
        self._after_create_or_update(context, resource)

    def before_update(self, context, current, resource):
        pass
    
    def after_update(self, context, resource):
        print('--Updated resource', resource['name'])
        self._after_create_or_update(context, resource)

    def before_delete(self, context, resource, resources):
        pass

    def after_delete(self, context, resource):
        print('--Deleted resource ', resource['name'])

    def before_show(self, resource_dict):
        return resource_dict

    # IPackageController

    def read(self, entity):
        pass
                       
    def create(self, entity):
        pass
 
    def edit(self, entity):
        pass

    def delete(self, entity):
        pass

    def _make_datacards_numeric(self, pkg_dict):
        def is_int(n):
          try:
            float_n = float(n)
            int_n = int(float_n)
          except ValueError:
            return False
          else:
            return float_n == int_n

        def is_float(n):
          try:
            float_n = float(n)
          except ValueError:
            return False
          else:
            return True

        for key in pkg_dict:
          if key.startswith("datacard") or key.startswith("extras_datacard"):
            value = pkg_dict[key]
            if is_int(value):
              value = int(value)
            elif is_float(value):
              value = float(value)
            print('--Found datacard key: ', key, ' with converted value: ', type(value))
            pkg_dict[key] = value
        return pkg_dict
                
    def after_show(self, context, pkg_dict):
        pass

    def before_search(self, search_params):
        #import re
        print('Before searching, params: ', search_params)
        #for (param, value) in search_params.items():
        #    print('Iterating over: ', (param, value))
        #    if type(value) == str and value.startswith('datacard') and '\"[' in value:
        #        v = re.sub(r'datacard([a-z_]*):\"*\"', r'datacard([a-z_]*):*', value)
        #        print('Modified param ', value, ' to value ', v)
        #        search_params[param] = v
        return search_params

    def after_search(self, search_results, search_params):
        return search_results

    def before_index(self, pkg_dict):
        print('Called before indexing')
        # Calling the following creates an infinite loop between IResourceController's package update and this.
        # return self._make_datacards_numeric(pkg_dict)
        return pkg_dict

    def before_view(self, pkg_dict):
        return pkg_dict

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        # Gathers all unique keys from datacard and add them to facets
        # DUMMY implementation below
        facets_dict[tk._('datacard_group1_metric')] = tk._('Resource Counts')
        return facets_dict

    #ITemplateHelpers
    
    def get_helpers(self):
        return {'datacard_fetch_grouped_datacard': fetch_grouped_datacard,
                'datacard_build_datacard_plot': build_datacard_plot}

