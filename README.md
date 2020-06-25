# datacard-ckan

- A CKAN extension which creates a data marketplace where one can manage datasets in their organization by means of **Data Cards**.
- **Data cards** represent a set of metadata for each dataset such that it could be used for diverse applications in data lakes, data marketplaces, data integration and so on.

# Setup guide

1. **CKAN setup**: Install CKAN in a Python virtual environment. This involves a number of steps including setting PostgreSQL and Redis. Follow the detailed guide linked here: https://docs.ckan.org/en/2.8/maintaining/installing/install-from-source.html. Mac users need to change a few steps as mentioned here: https://github.com/ckan/ckan/wiki/CKAN-installation-on-macOS-High-Sierra.

2. **Datacard extension**: Install ckanext-datacard by following instructions provided in [README](https://github.com/qcri/datacard-ckan/blob/master/ckanext-datacard/README.rst).

3. **Datacard generation**: Data cards are generated automatically as soon as a dataset is uploaded. However, the generation process runs as a background job for which at least one Redis worker process need to be initialized before launching CKAN site. As an example, if using paster in CKAN setup, one may use the following command after starting Redis server:
   ```
   paster jobs worker --config=/etc/ckan/default/development.ini datacard &
   #'datacard' is the name of the worker queue where the background jobs will go to.
   ```
   The second requirement for datacard generation is that the server should have R software installed which is used to generate some of the datacard   metrics. Prior to uploading any data, the following command should be executed in R. [[Reference](https://github.com/lpfgarcia/ECoL)]
   ```
   install.packages("ECoL")
   ```
4. **Dataset upload**: Datasets can be uploaded using the user interface provided in the website. We additionally provide a script to quickly perform this action. The script inputs a config file specifying both the access parameters to CKAN site and the details of dataset to be uploaded. A template is provided in the [source](https://github.com/mayureshkunjir/datacard-ckan/blob/master/config.ini.template). Invoke the script as:
   ```
   python uploadToCKAN.py <path to config.ini>
   ```
