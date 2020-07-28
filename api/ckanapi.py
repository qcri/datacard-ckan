#!/usr/bin/env python
from urllib.request import Request, urlopen
import requests
import urllib
import json
import pprint

class CKAN():

    def __init__(self, site, authorization, organization="qcri"):
        self.site = site
        self.key = authorization
        self.organization = organization

    def _buildheaders(self, auth_key='Authorization'):
        # Creating a dataset requires an authorization header.
        # Replace *** with your API key, from your user account on the CKAN site
        # that you're creating the dataset on.
        headers = {auth_key: self.key,
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                   'Accept-Encoding': 'none',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Connection': 'keep-alive'}
        return headers
        
    def _postrequest(self, url, data_dict, headers):
        data = json.dumps(data_dict).encode('utf8')
        # Make the HTTP request.
        request = Request(url, data, headers, method='POST')
        try:
            response = urlopen(request)
            # Use the json module to load CKAN's response into a dictionary.
            response_dict = json.loads(response.read())
            assert response_dict['success'] is True

            # package_create returns the created package as its result.
            result = response_dict['result']
            return result
        except urllib.error.URLError as e:
            print(e.code)
            print(e.read())
            return None

    def _postrequest_files(self, url, data_dict, headers, files):
        try:
            response = requests.post(url, data=data_dict, headers=headers, files=files)
            assert json.loads(response.content)['success'] is True
            result = json.loads(response.content)['result']
            return result
        except urllib.error.URLError as e:
            print(e.code)
            print(e.read())
            return None

    def _to_extras(self, kvs):
        extras = list()
        if not kvs:
            return extras
        for (k, v) in kvs.items():
            extra = {}
            extra['key'] = k
            extra['value'] = v
            extras.append(extra)
        return extras
        
    def getOrganization(self, name):
        url = self.site + '/api/action/organization_show'
        data_dict = {
            'id': name
        }
        result = self._postrequest(url, data_dict,self._buildheaders())
        # Package ID of the newly created resource
        if result is not None:
            print('Found organization: ', result['id'])
            return result['id']
        
    def getPackage(self, name):
        url = self.site + '/api/action/package_show'
        data_dict = {
            'id': name
        }
        result = self._postrequest(url, data_dict,self._buildheaders())
        # Package ID of the newly created resource
        if result is not None:
            print('Found package: ', result['id'])
            return result['id']
        
    def createOrganization(self, name, description, metadata):
        url = self.site + '/api/action/organization_create'
        data_dict = {
            'name': name,
            'description': description,
            'extras': self._to_extras(metadata)
        }
        print('creating organization: ', name, ' with: ', data_dict)
        result = self._postrequest(url, data_dict,self._buildheaders())
        # Package ID of the newly created resource
        if result is not None:
           print('Created organization: ', result['id'])
           return result['id']

    # name: Name of the dataset
    # organization: Name of the organization
    # type: Type of the dataset, e.g. 'mltype'
    # description
    # metadata: Custom datacards can be added here
    def createPackage(self, name, organization='qcri', type='mltype', description='NA', metadata=None):
        url = self.site + '/api/action/package_create'
        data_dict = {
            'name': name,
            'notes': description,
            'owner_org': organization,
            'type': type,
            'extras': self._to_extras(metadata)
        }
        print('creating package: ', name, ' with: ', data_dict)
        result = self._postrequest(url, data_dict,self._buildheaders())
        # Package ID of the newly created resource
        if result is not None:
           print('Created package: ', result['id'])
           return result['id']

    def deletePackage(self, name):
        url = self.site + '/api/action/package_delete'
        data_dict = {
            'id': name
        }
        print('deleting package: ', url, ' with: ', data_dict)
        result = self._postrequest(url, data_dict, self._buildheaders('X-CKAN-API-Key'))
        # Package ID of the newly created resource
        if result is not None:
           print('Deleted package: ', result)
           return result

    def createResource(self, package_id, name):
        url = self.site + '/api/action/resource_create'
        data_dict = {"package_id": package_id, "name": name}
        result = self._postrequest(url, data_dict, self._buildheaders())
        print('Created resource: ', result['id'])
        # Resource ID of the newly created resource
        if result is not None:
            return result['id']
        
    def addToResource(self, resource_id, df):
        url = self.site + '/api/action/datastore_create'
        # HACK: forcing data types to text
        df = df.applymap(str)
        fields = []
        for col in df.columns:
            fields.append({'id':col, 'type': 'text'})

        data_dict = {
            "resource_id": resource_id,
            "fields": fields,
            "records": df.to_dict(orient='records'),
            "force": True
        }
        result = self._postrequest(url, data_dict, self._buildheaders())
        # Resource ID where the insert happened
        if result is not None:
            return result['resource_id']
        
    def createAndAddResource(self, package_id, name, df):
        url = self.site + '/api/action/datastore_create'
        # HACK: forcing data types to text
        df = df.applymap(str)
        fields = []
        for col in df.columns:
            fields.append({'id':col, 'type': 'text'})

        print('adding to datastore: ', name, ' with df of shape: ', df.shape)
        data_dict = {
            "resource": {"package_id":package_id, "name":name},
            "fields": fields,
            "records": df.to_dict(orient='records'),
            "force": True
        }
        result = self._postrequest(url, data_dict, self._buildheaders())
        # Resource ID where the insert happened
        if result is not None:
            return result['resource_id']

    def uploadFile(self, package_id, name, filepath):
        url = self.site + '/api/action/resource_create'
        print('uploading to file store: ', name, ' file from: ', filepath)
        files = [('upload', open(filepath, 'rb'))]
        data_dict = {
            "package_id":package_id,
            "name":name
        }
        result = self._postrequest_files(url, data_dict, self._buildheaders('X-CKAN-API-Key'), files)
        # Resource ID where the insert happened
        if result is not None:
            print('Uploaded file: ', result)
            return result['id']

    def compute_datacard(self, package_id):
        url = self.site + '/api/action/compute_datacard'
        print('creating datacards for dataset identified by: ', package_id)
        data_dict = {
            "id":package_id,
        }
        result = self._postrequest(url, data_dict, self._buildheaders())
        return result

    def get_datacard(self, package_id):
        url = self.site + '/api/action/get_datacard'
        print('fetching datacards for dataset identified by: ', package_id)
        data_dict = {
            "id":package_id,
        }
        result = self._postrequest(url, data_dict, self._buildheaders())
        return result

    '''
    Key should be of format <group>_<metric>
    '''
    def search_datacard(self, key, value):
        url = self.site + '/api/action/search_datacard'
        print(f'searching datasets for query: {key}={value}')
        data_dict = {
            "key": key, "value": value
        }
        result = self._postrequest(url, data_dict, self._buildheaders())
        return result
