# datacard-ckan

- A CKAN extension to be used as a backend service for **Data Cards**.
- **Data cards** represent a set of metadata for each dataset such that it could be used for diverse applications in data lakes, data marketplaces, data integration and so on.

# Setup guide

1. **CKAN setup**: Install CKAN in a Python virtual environment. This involves a number of steps including setting PostgreSQL and Redis. Follow the detailed guide linked here: https://docs.ckan.org/en/2.8/maintaining/installing/install-from-source.html. Mac users need to change a few steps as mentioned here: https://github.com/ckan/ckan/wiki/CKAN-installation-on-macOS-High-Sierra.

2. **Datacard extension**: Install ckanext-datacard_backend by following instructions provided in [README](https://github.com/qcri/datacard-ckan/blob/backend/ckanext-datacard_backend/README.rst).

3. **Datacard generation**: Data cards generation process runs as a background job for which at least one Redis worker process need to be initialized before launching CKAN site. As an example, if using paster in CKAN setup, one may use the following command after starting Redis server:
   ```
   paster jobs worker --config=/etc/ckan/default/development.ini datacard &
   #'datacard' is the name of the worker queue where the background jobs will go to.
   ```
   The second requirement for datacard generation is that the server should have R software installed which is used to generate some of the datacard   metrics. Prior to uploading any data, the following command should be executed in R. [[Reference](https://github.com/lpfgarcia/ECoL)]
   ```
   install.packages("ECoL")
   ```
# API guide

- Regular REST-based CKAN APIs are available which can be used for functionalities such as creating a package or uploading a dataset file. Please refer to the [docs](https://docs.ckan.org/en/2.8/api/index.html).
- Additionally, our extension provides the following APIs:
    1. compute_datacard(id): 'id' corresponds to the package id of the CKAN dataset
    2. get_datacard(id): 'id' corresponds to the package id of the CKAN dataset
    3. search_datacard(key, value): supports search query of the type 'key'='value'. The key should be of format <group><metric> 
- Examples of using Python interface can be found in the file [ckanapi.py](https://github.com/qcri/datacard-ckan/blob/backend/api/ckanapi.py)
- An example of using HTTP request to make API request is given below:
    ```
    http://127.0.0.1:5050/api/3/action/search_datacard?key=overlapping_F2.mean&value=1.0
    ```
