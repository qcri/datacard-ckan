import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ast
import os
import json
import pandas as pd
import numpy as np
import collections

# Need to import these because of code copied from helpers.py
from six import string_types
from urllib import urlencode

from ckan.common import config, request
from generators.mlgenerator import MLDatacardGenerator
from compare import generate_datacard_plot, generate_datacard_spreadsheet

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

def _fetch_grouped_datacard(pkg_dict):
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

def _read_package(package_id):
    data_dict = {
        'id': package_id
    }
    pkg_dict = tk.get_action('package_show')(None, data_dict)
    return pkg_dict

# packages is a list of package dicts in unicode when ids=False
# else it is a list of package ids in unicode
def _build_grouped_dataframe(packages, ids=False):
    # Schema for dataframe for each group: ( package, metric1, metric2, ...)
    groupedDF = {}
    # fetch grouped datacard from each pkg dict
    pkglist = []
    groups = []
    metrics = {}

    if(not ids):
      try:
        for pkg in ast.literal_eval(packages):
            pkgname = pkg['name']
            # print('-- Getting package: ', pkgname)
            metrics[pkgname] = _fetch_grouped_datacard(pkg)
            pkglist.append(pkgname)
            groups.extend(metrics[pkgname].keys())
      except ValueError:
        # print('Trying out with a single package: ', packages)
        # this is likely a single package requested in dataset page
        try:
            pkg = packages
            pkgname = pkg['name']
            # print('-- Getting package: ', pkgname)
            metrics[pkgname] = _fetch_grouped_datacard(pkg)
            pkglist.append(pkgname)
            groups.extend(metrics[pkgname].keys())
        except Exception as e:
            print(e)
            return (None, None)# can't help with this exception
    else:
      # when package ids are passed
      try:
        for pkg_id in ast.literal_eval(packages):
            pkg_dict = _read_package(pkg_id)
            pkgname = pkg_dict['name']
            # print('-- Getting package: ', pkgname)
            metrics[pkgname] = _fetch_grouped_datacard(pkg_dict)
            pkglist.append(pkgname)
            groups.extend(metrics[pkgname].keys())
      except ValueError as e:
          print(e)
          return (None, None)
        
    # merge the data from packages to create a dataframe
    groups = set(groups)
    # Ignore test groups
    groups = [x for x in groups if not x.startswith('group')]
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
            record = collections.OrderedDict()
            record['Dataset'] = pkg
            for k, v in sorted(groupData.iteritems()):
                record[k] = v
            # print('-- Record data: ', record)
            recordlist.append(record)
    
        df = pd.DataFrame(recordlist)
        # print('-- Creating grouped dataframe for ', group, ' : ', df)
        # Transform to numeric whenever possible taking care of nan values
        df = df.replace('NaN', np.nan).fillna('')
        # print('-- before numeric: ', df)
        numDF = df.apply(pd.to_numeric, errors='ignore')
        # print('-- after numeric: ', numDF)
        groupedDF[group] = numDF

    return (groupedDF, groups)

# packages is a list of package dicts in unicode
def build_datacard_plot(packages):
    (groupedDF, groups) = _build_grouped_dataframe(packages)
    # build a plot with slider to select a group
    if groupedDF and groups:
        return generate_datacard_plot(groupedDF, groups)
    return None

def build_datacard_spreadsheet(packages):
    ids = True # by default package ids are passed
    if isinstance(packages, dict):
        ids = False # package dictionary passed
    (groupedDF, groups) = _build_grouped_dataframe(packages, ids)
    # build a plot with slider to select a group
    if groupedDF and groups:
        return generate_datacard_spreadsheet(groupedDF, groups)
    return None

# Built as a wrapper over tk.h.get_facet_items_dict
# Bins numeric facets to only four non-overlapping range intervals
def get_facet_items_binned(facet, limit=None, exclude_active=False):

    from itertools import islice
    
    def histedges_equalN(x, nbin):
        npt = len(x)
        return np.interp(np.linspace(0, npt, nbin + 1),
                         np.arange(npt),
                         np.sort(x))

    def window(seq, n=2):
        "Returns a sliding window (of width n) over data from the iterable"
        "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
        it = iter(seq)
        result = tuple(islice(it, n))
        if len(result) == n:
            yield result    
        for elem in it:
            result = result[1:] + (elem,)
            yield result

    # items = tk.h.get_facet_items_dict(facet, limit, exclude_active)
    if not hasattr(tk.c, u'search_facets') or not tk.c.search_facets.get(
                                               facet, {}).get(u'items'):
        return []

    # Set filters active even when they do not match the exact condition
    items = []
    requests = request.params.items()
    active_facets = []
    # print('-- requested: ', requests)
    for r in requests:
        if(r[0] == 'q'): # case of q=...
            queries = r[1].split(' AND ') # Assuming queries are separated by AND
            active_facets = [ q.split(':')[0] for q in queries ]
    # print('-- active facets: ', active_facets)
    
    for facet_item in tk.c.search_facets.get(facet)['items']:
        if not len(facet_item['name'].strip()):
            continue
        if not exclude_active and facet in active_facets:
            # print('Active = ', facet_item)
            items.append(dict(active=True, **facet_item))
        else:
            # print('Not active = ', facet_item)
            items.append(dict(active=False, **facet_item))
    # Sort descendingly by count and ascendingly by case-sensitive display name
    items.sort(key=lambda it: (-it['count'], it['display_name'].lower()))
    if hasattr(tk.c, 'search_facets_limits'):
        if tk.c.search_facets_limits and limit is None:
            limit = tk.c.search_facets_limits.get(facet)
    # zero treated as infinite for hysterical raisins
    if limit is not None and limit > 0:
        items = items[:limit]
    
    # print('-- Facet name passed: ', facet, ' found items: ', len(items), ' with type: ', type(items))
    chosenItems = []
    toBeProcessedItems = []
    numBins = 3
    numCategoricalBins = 0
    values = []
    counts = []
    if(len(items) > numBins):
        for item in items:
            # print('-- Looking at ', item)
            value = item['name']
            try:
                value = float(item['name'])
                if(np.isnan(value)):
                    #print('NaN encountered')
                    chosenItems.append(item)
                    numCategoricalBins += 1
                else:
                    values.append(value) # candidate for histogram
                    counts.append(item['count'])
                    toBeProcessedItems.append(item)
            except ValueError as e:
                print(e)
                chosenItems.append(item)
                numCategoricalBins += 1

        numBinsLeft = numBins - numCategoricalBins
        if(numBinsLeft > 0):
            hist, ranges = np.histogram(values, histedges_equalN(values, numBinsLeft))
            # print('-- Obtained histogram: ', hist, ' with: ', ranges, ' and intervals: ', np.digitize(values, ranges))
            for (start, end) in window(ranges):
                display_name = '{:.2f}'.format(start) + ':' + '{:.2f}'.format(end)
                chosenItems.append({'count': 0, 'active': False, 'display_name':tk._(display_name) , 'name': tk._(display_name), 'start': start, 'end': end, 'right_closed': True}) #TODO: Change right_closed to False

            i = 0
            for histindex in np.digitize(values, ranges):
                if(histindex == len(hist) + 1): # because intervals are open ended on right
                    histindex = histindex - 1
                    chosenItems[numCategoricalBins + histindex - 1]['right_closed'] = True
                chosenItems[numCategoricalBins + histindex - 1]['count'] += counts[i]
                #print('Adding ', counts[i], ' to bin: ', numCategoricalBins+histindex-1)
                i += 1
        print('Chosen items: ', chosenItems)
        return chosenItems
    return items

# HACK: Copied private method from tk.h
def _url_with_params(url, params):
    if not params:
        return url
    params = [(k, v.encode('utf-8') if isinstance(v, string_types) else str(v))
              for k, v in params]
    return url + u'?' + urlencode(params)

# HACK: Copied private methodd from tk.h
def _create_url_with_params(params=None, controller=None, action=None,
                            extras=None):
    ''' internal function for building urls with parameters. '''

    if not controller:
        controller = tk.c.controller
    if not action:
        action = tk.c.action
    if not extras:
        extras = {}

    url = tk.h.url_for(controller=controller, action=action, **extras)
    return _url_with_params(url, params)

# Built over tk.h.add_url_param
# Add 'new_params' to query string
def datacard_add_url_param(alternative_url=None, controller=None, action=None,
                  extras=None, new_params=None):
    params_nopage = [(k, v) for k, v in request.params.items() if k != 'page']
    params = list(params_nopage)
    # print('--Existing params: ', params)
    # print('--New params: ', new_params)
    if new_params:
        if len(params) == 0:
            params.append(('q', new_params))
        else:
            newQuery = None
            for p in params:
                if(p[0] == 'q'):
                    newQuery = p[1] + ' AND ' + new_params
            if(newQuery):
                params = [('q', newQuery) if p[0]=='q' else p for p in params]

    if alternative_url:
        return _url_with_params(alternative_url, params)

    return _create_url_with_params(params=params, controller=controller,
                                   action=action, extras=extras)

# Built over tk.h.remove_url_param
# If 'new_params' is in query string, remove it, else update it with new value
def datacard_update_url_param(key, value=None, replace=None, controller=None,
                              action=None, extras=None, alternative_url=None, new_params=None):
    if isinstance(key, string_types):
        keys = [key]
    else:
        keys = key

    params_nopage = [(k, v) for k, v in request.params.items() if k != 'page']
    params = list(params_nopage)
    active_queries = []
    for p in params:
        if(p[0] == 'q'):
            active_queries = [tuple(query.split(':')) for query in p[1].split(' AND ')]

    if value:
        active_queries.remove((keys[0], value))
    else:
        for key in keys:
            [active_queries.remove((k, v)) for (k, v) in active_queries if k == key]
        print('--Active queries after removal: ', active_queries)
    if replace is not None:
        active_queries.append((keys[0], replace))

    if len(active_queries) > 0:
        unjoined = [k + ':' + v for (k, v) in active_queries]
        joined = ' AND '.join(unjoined)
        print('--Queries after removal: ', joined)
        params = [('q', joined) if p[0]=='q' else p for p in params]
    else: #All queries eliminated
        [params.remove((k, v)) for (k, v) in params if k == 'q']

    if new_params:
        if len(params) == 0:
            params.append(('q', new_params))
        else:
            newQuery = None
            for p in params:
                if(p[0] == 'q'):
                    newQuery = p[1] + ' AND ' + new_params
            if(newQuery):
                params = [('q', newQuery) if p[0]=='q' else p for p in params]

    if alternative_url:
        return _url_with_params(alternative_url, params)

    return _create_url_with_params(params=params, controller=controller,
                                   action=action, extras=extras)


class DatacardPlugin(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceController)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IPackageController)
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
        return ['mltype']

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
        return schema

    def setup_template_variables(self, context, data_dict):
        return super(DatacardPlugin, self).setup_template_variables(
                context, data_dict)

    # IResourceController
  
    def _after_create_or_update(self, context, resource):
        if 'size' not in resource:
            return # This is a package update; we are only interested in resource update. Open issue at: https://github.com/ckan/ckan/issues/2949
        url = resource['url']
        print('--Modified resource at ', {url}, ' from package ', context['package'])
        # Invoke each generator in a separate background job
        generator = MLDatacardGenerator(resource['package_id'])
        job = tk.enqueue_job(generator.generate, queue=tk._('datacard'))

    def before_create(self, context, resource):
        pass

    def after_create(self, context, resource):
        self._after_create_or_update(context, resource)

    def before_update(self, context, current, resource):
        pass
    
    def after_update(self, context, resource):
        self._after_create_or_update(context, resource)

    def before_delete(self, context, resource, resources):
        pass

    def after_delete(self, context, resource):
        pass

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
        # print('Before searching, params: ', search_params)
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
        print('--Called before indexing')
        # Delete keys starting with 'datacard_' from dict
        deleteKeys = [key for key in pkg_dict if key.startswith('datacard')]
        for key in deleteKeys:
            print('--Deleting: ', key)
            del pkg_dict[key]
        
        # Fetch extras from dict
        extras_dict = json.loads(pkg_dict['data_dict'])['extras']
        # print('-- extras: ', extras_dict)
        extras_list = tk.h.sorted_extras(extras_dict)

        # Insert keys from extras starting with datacard_ again
        for (k, v) in extras_list:
            pkg_dict[k] = float(v)
            print('-- Adding: ', k, ' -> ', float(v))
         
        # return self._make_datacards_numeric(pkg_dict)
        return pkg_dict

    def before_view(self, pkg_dict):
        return pkg_dict

    # IFacets
    cachedFacets = {}

    def dataset_facets(self, facets_dict, package_type):
        print('Requested facets for: ', package_type, ' facets: ', facets_dict)
        del facets_dict['organization']
        del facets_dict['groups']
        del facets_dict['tags']

        package_type = 'mltype' # FIXME: Hacking, need to see why CKAN is not passing this value
        if(package_type in self.cachedFacets):
            facets_dict.update(self.cachedFacets[package_type])
            return facets_dict
        
        # Gathers all unique keys from datacard and add them to facets
        self.cachedFacets[package_type] = collections.OrderedDict()
        facetsconf_dict = config.get('ckan.datacard.facetsdict', None)
        # print('Looking through folder: ', facetsconf_dict)
        if facetsconf_dict is not None:
            facets_file = os.path.join(facetsconf_dict, package_type)
            # print('looking for: ', facets_file)
            if os.path.exists(facets_file):
                # print('Reading from: ', facets_file)
                data = pd.read_csv(facets_file, sep='\t', index_col='Metric', usecols=('Metric', 'DisplayValue'))
                print('Obtained new facets: ')
                for row in data.itertuples():
                    print(row)
                    self.cachedFacets[package_type][tk._(row[0])] = tk._(row[1])
        # DUMMY implementation below
        self.cachedFacets[package_type][tk._('datacard_group1_metric')] = tk._('Resource Counts')
        facets_dict.update(self.cachedFacets[package_type])
        return facets_dict

    #ITemplateHelpers
    
    def get_helpers(self):
        return {'datacard_fetch_grouped_datacard': _fetch_grouped_datacard,
                'datacard_build_datacard_plot': build_datacard_plot,
                'datacard_build_datacard_spreadsheet': build_datacard_spreadsheet,
                'datacard_get_facet_items_dict': get_facet_items_binned,
                'datacard_add_url_param': datacard_add_url_param,
                'datacard_update_url_param': datacard_update_url_param
        }

