

#####################################################################################
#
#   Google CloudML
#
#####################################################################################


# List CloudML Models
gcloud ml-engine models list


# Set ENV Variables
PROJECT_ID=$(gcloud config list project --format "value(core.project)")
BUCKET_NAME=${PROJECT_ID}-mlengine
REGION=us-east1


# Create a GCS Bucket to use with CloudML
gsutil mb -l $REGION gs://$BUCKET_NAME






Specific to GCP, traction with the Red Hat teams has been slow and we could use executive support to get infront of the right teams at Red Hat. We believe that opportunities exist with the product teams.



There is a $400k GCP opportunity in the POC stage (Global Replicator). Aside from that, traction with the Red Hat teams has been slow and we could use executive support to get infront of the right teams at Red Hat. We believe that opportunities exist with the product teams.








########################################################################################################
#
#   Sklean Model
#
########################################################################################################

import os,sys,csv,re
import time,datetime
import argparse

import pandas as pd
import numpy as np
import scipy as sp
import pickle
import subprocess

from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, median_absolute_error, explained_variance_score
from sklearn.externals import joblib

########################################################################################################
#
#   Input Data
#
########################################################################################################

# Read local CSV
def load_rawdata(training_data):
    '''
        USAGE:
            rawdata = load_rawdata(training_data='./data/nfldata2.csv')
            rawdata = load_rawdata(training_data='/tmp/nfldata2.csv')
    '''
    try:
        training_data = re.sub('^\.' , os.getcwd() , training_data)
        print('[ INFO ] Reading in NFL Training data from from {}'.format(training_data))
        time.sleep(3)
        
        header  = ['Date', 'GameID', 'Drive', 'qtr', 'down', 'time', 'TimeUnder', 'TimeSecs', 'PlayTimeDiff', 'yrdline100', 'ydstogo', 'ydsnet', 'FirstDown', 'posteam', 'DefensiveTeam', 'Yards_Gained', 'Touchdown', 'PlayType', 'PassLength', 'PassLocation', 'RunLocation', 'PosTeamScore', 'DefTeamScore', 'month_day', 'PlayType_lag']
        rawdata = pd.read_csv(training_data , names=header)
        # Quickly explore data structure
        rawdata.head()
        #rawdata.values
        rawdata.iloc[0]
        rawdata.shape
        rawdata.columns
        rawdata.dtypes
        rawdata.describe()
        print('[ INFO ] Read in training_data located at {}'.format(training_data))
        return rawdata
    except:
        print('[ ERROR ] Could not find training_data. Check directory path and filename, then try again.')
        #sys.exit()

########################################################################################################
#
#   Transformations
#
########################################################################################################

def transform_df(rawdata, target_variable_name):
    
    # Model Variables (Specify id, target, numeric variables, and categorical variables)
    var_id              = ''
    var_target          = target_variable_name #'Yards_Gained'
    var_date            = 'Date'
    var_numeric         = ['Drive', 'qtr', 'down', 'TimeSecs', 'PlayTimeDiff', 'yrdline100', 'ydstogo', 'ydsnet', 'FirstDown', 'PosTeamScore', 'DefTeamScore', 'month_day', ]
    var_category        = ['posteam', 'DefensiveTeam','PlayType','PlayType_lag']
    
    transformed_set             = {}
    transformed_set[var_target] = rawdata[var_target]
    
    for var in var_numeric:
        transformed_set[var] = rawdata[var]
    
    '''
    for var in var_category:
        transformed_set[var] = rawdata[var].astype('category').cat.codes
    '''
    
    category_coding = {}
    for var in var_category:
        category_coding[var] = dict( enumerate( rawdata[var].astype('category').cat.categories ))
        transformed_set[var] = rawdata[var].astype('category').cat.codes
    
    extracted_year  = pd.to_datetime(rawdata[var_date]).dt.year
    extracted_month = pd.to_datetime(rawdata[var_date]).dt.month
    extracted_day   = pd.to_datetime(rawdata[var_date]).dt.day
    
    transformed_set['year']  = extracted_year
    transformed_set['month'] = extracted_month
    transformed_set['day']   = extracted_day
    
    # Create transformed DF
    transformed_df = pd.concat([v for k,v in transformed_set.items()], axis=1)
    transformed_df.columns = [k for k,v in transformed_set.items()]
    transformed_df.head()
    return transformed_df

########################################################################################################
#
#   Train and Test DFs
#
########################################################################################################

def partition_df(transformed_df, target_variable_name):
    
    random_number  = pd.DataFrame(np.random.randn(len(transformed_df), 1))
    partition_mask = np.random.rand(len(random_number)) <= 0.75
    
    train_data     = transformed_df[partition_mask]
    test_data      = transformed_df[~partition_mask]
    
    train_data.shape
    test_data.shape
    
    train_inputs   = train_data.drop([target_variable_name], axis=1)
    train_target   = train_data[target_variable_name]
    
    test_inputs    = test_data.drop([target_variable_name], axis=1)
    test_target    = test_data[target_variable_name]
    
    return train_inputs, train_target, test_inputs, test_target

########################################################################################################
#
#   Gradient Boosting Model (Regression)
#
########################################################################################################

def train_model(train_inputs, train_target, test_inputs, number_of_estimators=100):
    
    model_obj = GradientBoostingRegressor(n_estimators=number_of_estimators, learning_rate=0.1, criterion='friedman_mse', max_depth=3, random_state=12345)
    print('[ INFO ] Training Gradient Boosting Regressor with {} estimators.'.format(number_of_estimators))
    time.sleep(1)
    starttime = datetime.datetime.now()
    model_obj.fit(train_inputs, train_target)
    total_runtime = (datetime.datetime.now() - starttime).seconds
    print('[ INFO ] Modeling complete! Total Runtime: {} seconds'.format(total_runtime))
    
    target_predicted = model_obj.predict(test_inputs)
    return model_obj, target_predicted

def evaluate_regression_model(actual, predicted):
    mse      = mean_squared_error(y_true=actual, y_pred=predicted)
    meanae   = mean_absolute_error(y_true=actual, y_pred=predicted)
    medianae = median_absolute_error(y_true=actual, y_pred=predicted)
    r2       = r2_score(y_true=actual, y_pred=predicted)
    #variance = explained_variance_score(y_true=actual, y_pred=predicted)
    
    print('[ INFO ] Mean Squared Error:     {}'.format(mse))
    print('[ INFO ] Mean Absolute Error:    {}'.format(meanae))
    print('[ INFO ] Median Absolute Error:  {}'.format(medianae))
    print('[ INFO ] R2 Score:               {}'.format(r2))

def save_model(model_obj):
    print('[ INFO ] Saving model locally in /tmp...')
    model_name  = 'nfl_model'
    bucket_name = 'z_mlbucket'
    joblib.dump(model_obj, '/tmp/{}.joblib'.format(model_name))
    print('[ INFO ] Model saved as /tmp/{}.joblib'.format(model_name))
    print('[ INFO ] Copying to Google Cloud Storage in 5 seconds...')
    time.sleep(5)
    subprocess.check_call(['gsutil', 'cp', '/tmp/{}.joblib'.format(model_name), 'gs://{}/{}.joblib'.format(bucket_name, model_name)], stderr=sys.stdout)
    print('[ INFO ] /tmp/{}.joblib upload to gs://{}/{}'.format(model_name, bucket_name, model_name))



if __name__ == "__main__"
    
    # Arguments (used only for testing)
    #args = {"training_data":"./data/nfldata2.csv", "target_variable_name":"Yards_Gained"}
    
    # Arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("--training_data",          required=True, type=str, help="Path to local training data")
    ap.add_argument("--target_variable_name",   required=True, type=str, help="Name of target / label variable")
    args = vars(ap.parse_args())
    
    # Load Dataset
    rawdata = load_rawdata(args['training_data'])
    
    # Transform / Prep dataframe
    transformed_df = transform_df(rawdata, args['target_variable_name'])
    
    # Split into train and test dataframes
    train_inputs, train_target, test_inputs, test_target = partition_df(transformed_df, args['target_variable_name'])
    
    # Train Model
    model_obj, target_predicted = train_model(train_inputs, train_target, test_inputs, number_of_estimators=100)
    
    # Evaluate Model
    evaluate_regression_model(actual=test_target, predicted=target_predicted)
    
    # Save Model
    save_model(model_obj)



#ZEND
