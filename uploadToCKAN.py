import configparser as parser
import os
import sys
from api.ckanapi import CKAN

def main(config_path):

    # Read config
    if(config_path is None or not os.path.exists(config_path)):
        print("Please provide a valid config file")

    config = parser.ConfigParser()
    config.read(config_path)
    
    site_url = ''
    api_key = ''
    if 'CKAN' in config.sections():
       site_url = config['CKAN']['site_url']
       api_key = config['CKAN']['api_key']

    organization = ''
    dataset = ''
    dataset_type = ''
    dataset_description = 'Data uploaded using uploadToCKAN API'
    dataset_file = ''
    if 'DATA' in config.sections():
       organization = config['DATA']['organization']
       dataset = config['DATA']['dataset.name']
       dataset_description = config['DATA']['dataset.description']
       dataset_type = config['DATA']['dataset.type']
       dataset_file = config['DATA']['dataset.file']

    # Validate config
    assert site_url
    assert api_key
    assert organization
    assert dataset
    assert dataset_description
    assert dataset_type
    assert dataset_file
    assert os.path.isfile(dataset_file)

    # Run API
    ckan = CKAN(site_url, api_key)

    org_id = ckan.getOrganization(organization)
    if org_id is None:
       org_id = ckan.createOrganization(organization, "description coming soon", {})

    package_id = ckan.getPackage(dataset)
    if package_id is None:
       package_id = ckan.createPackage(dataset, organization, dataset_type, dataset_description)
    if(package_id is not None):
       ckan.uploadFile(package_id, os.path.basename(dataset_file), os.path.normpath(dataset_file))

if __name__ == "__main__":

    # Usage: python uploadToCKAN.py <CONFIG_PATH>
    config_path = 'config.ini'
    if len(sys.argv) >= 2:
        config_path = sys.argv[2]
    main(config_path)
