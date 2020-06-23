import pandas as pd
from . import DatacardGenerator

from scipy.io import arff
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri

import requests
import io, traceback

class MLDatacardGenerator(DatacardGenerator):

    def __init__(self, package):
        DatacardGenerator.__init__(self, package)

    # dummy implementation
    def is_arff(self, resource_url):
        print('** Checking url: ', resource_url)
        return resource_url.endswith('.arff')

    # dummy implementation
    def is_csv(self, resource_url):
        return resource_url.endswith('.csv')
        
    def generateLocalMetrics(self, resource_url):
        # read pandas dataframe
        df = pd.DataFrame()
        try:
            response = requests.get(resource_url)
            content = io.StringIO(response.content.decode('utf-8'))
            if self.is_arff(resource_url):
                data, meta = arff.loadarff(content)
                print('*** arff data: ', meta)
                df = pd.DataFrame(data)
                # print('*** Loaded df: ', df)
                # The following two changes are needed to make the dataframe workable with R
                strcols = df.select_dtypes(exclude=['number']).columns
                df.loc[:, strcols] = df.loc[:, strcols].applymap(lambda x: x.replace("'", ""))
                numcols = df.select_dtypes(include=['number']).columns
                df.loc[:, numcols] = df.loc[:, numcols].astype('object')
            if self.is_csv(resource_url):
                df = pd.read_csv(content) # not tested yet
        except Exception as e:
            traceback.print_exc()
            print('Exception caught: ', e)

        print('*** Workable df with R: ', df, ' types: ', df.dtypes)

        # convert to R dataframe
        # Assuming that the last column is the output values
        pandas2ri.activate()
        # print('** pandas2ri methods: ', dir(pandas2ri))
        # Latest pyr2 docs recommend to use pandas2ri.py2ri functionality, but we are not able to use latest version of pyr2 due to dependence on python 2 forced by CKAN. The following works for pyr2=2.4.0, not tested on other versions.
        inputD = pandas2ri.pandas2ri(df)
        print('** Input dataframe: ', inputD)
        # inputR = pandas2ri.pandas2ri(df.iloc[:, :-1])
        # outputR = pandas2ri.pandas2ri(df.iloc[:, -1:])

        # Call R functions on dataframe
        ro.r('require(ECoL)')
        ro.globalenv['dat'] = inputD
        ## Conversion from pandas sets column types to StrVector, we need them to be FactorVectors in the APIs we invoke.
        ro.r('''dat[,1:ncol(dat)]=lapply(1:ncol(dat),function(x) {
        tryCatch({
        as.factor(dat[[x]])
        },warning = function(w) {
        dat[[x]]}
        )} )''')
        # ro.globalenv['xvar'] = inputR
        # ro.globalenv['yvar'] = outputR
        # result = ro.r('complexity(xvar, yvar)')
        ## For the lack of knowledge of input data, we are making an assumption that the last column of dataset is the dependent attribute.
        result = ro.r('complexity(dat[-ncol(dat)], dat[ncol(dat)])')
        print('*** Complexity output: ', pandas2ri.ri2pandas(result), ' type: ', dir(result))
        for name in result.names:
            print('** Datacard metric: ', name, ' -> ', result.rx2(name)[0])
            group, metric = name.split('.', 1)
            value = result.rx2(name)[0]
            self.add_to_datacard(group, metric, value)

    def generateGlobalMetrics(self):
        # Working under the assumption that the dataset contains only one file, so all the work has been done by the local metrics
        pass


