import ckan.plugins.toolkit as tk

class DatacardGenerator:
    
    def __init__(self, package):
        self.datacard = {}
        self.package = package

    def read_resource(self, resource_id):
        pass

    def read_package(self, package_id):
        data_dict = {
            'id': package_id
        }
        pkg_dict = tk.get_action('package_show')(None, data_dict)
        return pkg_dict

    def update_package(self, data_dict):
        pkg_dict = tk.get_action('package_update')(None, data_dict)
        return pkg_dict

    def generateLocalMetrics(self, resource_url):
        raise NotImplementedError

    def generateGlobalMetrics(self):
        raise NotImplementedError

    def add_to_datacard(self, group, key, value):
        dckey = "datacard_" + group + "_" + key
        self.datacard[dckey] = value
    
    def generate(self):
        result = self.read_package(self.package)
        extras = []
        urls = []
        resourceIds = []
        if result is not None:
            for resource in result['resources']:
                urls.append(resource['url'].encode('utf8'))
                resourceIds.append(resource['id'])
            extras = list(result['extras'])
            del result['extras'] # no longer needed

        # remove old datacard from extras 
        print('*** Extras fetched: ', extras)
        existingDatacards = []
        for extra in extras:
            if extra['key'].startswith(u'datacard_'):
                existingDatacards.append(extra)
        for extra in existingDatacards:
            extras.remove(extra)
        print('*** Extras after removal: ', extras)

        # generate local datacard
        for url in urls:
            self.generateLocalMetrics(url)
        # generate global datacard
        self.generateGlobalMetrics()

        # add to extras
        for (k, v) in self.datacard.items():
            newExtra = {}
            newExtra[u'key'] = k
            newExtra[u'value'] = v
            extras.append(newExtra)
        print('*** Extras after addition: ', extras)
        result['extras'] = extras

        # call api to upload datacard as extras
        self.update_package(result)
