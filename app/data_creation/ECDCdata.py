# for data managaement
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta

# for charting
import plotly
import plotly.graph_objects as go
from sklearn.metrics import mean_squared_error, r2_score

# colours
#from palettable.colorbrewer.qualitative import Paired_12
from palettable.tableau import Tableau_20


# for dash app
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

# for scraping data
import bs4
import requests
import boto3

from config import ACCESS_KEY,SECRET_KEY
# define functions


def make_chart_data(country):
    ''' makes a seperate dataset for a country
        takes country name as input '''
    chart_data = data.loc[data['countriesAndTerritories']
                          == country].reset_index()
    return chart_data

# shifts the data to 'day 0 of the corona virus'


def reindex(df, var, index_=10):
    ''' creates a data series which shifts data so that the day
    where the criteria index_ is reached is at index 0
    Note cases are indexed to weekly total, while deaths to cumulative total'''
    dta = df.copy()

    # First we need to identify the day at which the minimum number of cases/deaths is reached
    # some countries have no data so the try/except allows the function to
    # ignore them
    try:
        first_day = dta[dta[var] > index_].index[0]

    # The cumulative cases/deaths data are then shifted back so that the first
    # day index_ is exceeded becomes index 0
        dta[var] = dta[var].shift(-first_day)
    except BaseException:
        dta[var] = np.nan
    return dta

def s3_upload(access_key,secret_key, write_path):

    s3 = boto3.client(
    "s3",
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key
    )
    bucket_resource = s3
    
    filename = write_path
    
    bucket_resource.upload_file(
    Bucket = 'covid-19-app-data',
    Filename=filename,
    Key=filename,
    ExtraArgs ={'ACL':'public-read'}
    )




# Data read in and feature creation/ data wrangling

data = pd.read_csv(
    'https://opendata.ecdc.europa.eu/covid19/casedistribution/csv',
    usecols=list(
        range(
            0,
            10)))

continents = pd.read_csv('https://covid-19-app-data.s3.eu-west-2.amazonaws.com/continents.csv')

# make datetime
data['dateRep'] = pd.to_datetime(data['dateRep'], dayfirst=True)

# sort values by country and date
data.sort_values(by=['countriesAndTerritories', 'dateRep'],
                 ascending=True, inplace=True)

# reindex the data now its sorted to prevent errors when creating aggregates
data = data.reindex()

# create a global aggregate figure for cases and deaths
world = data[['dateRep', 'cases', 'deaths',
              'popData2019']].groupby(by='dateRep').sum()

world['day'] = world.index.day
world['month'] = world.index.month
world['year'] = world.index.year
world['dateRep'] = world.index
world['countriesAndTerritories'] = 'World'
world['geoId'] = 'WD'
world['countryterritoryCode'] = 'WLD'
data = pd.concat([data, world], ignore_index=True)

# Create a continents var

data = pd.merge(data,
                continents[['Continent_Name',
                            'Three_Letter_Country_Code']].drop_duplicates('Three_Letter_Country_Code'),
                how='left',
                left_on='countryterritoryCode',
                right_on='Three_Letter_Country_Code')
# create cumulative sum of deaths and cases by country and death rate
data['total_cases'] = data.groupby(by='countriesAndTerritories')[
    'cases'].cumsum()
data['total_deaths'] = data.groupby(by='countriesAndTerritories')[
    'deaths'].cumsum()

# create 7 day rolling average of deaths and cases


data['deaths_7_day_sum'] = data.groupby(by=['countriesAndTerritories'])[
    'deaths'].rolling(7).sum().values
data['cases_7_day_sum'] = data.groupby(by=['countriesAndTerritories'])[
    'cases'].rolling(7).sum().values
data['death_rate'] = data['total_deaths'] / data['total_cases'] * 100

# Create cumulative deaths and cases per capita
data['deaths_per_cap'] = data['total_deaths'] / data['popData2019']
data['cases_per_cap'] = data['total_cases'] / data['popData2019']

# create death rates variable
data['death_rate'] = data['total_deaths'] / data['total_cases'] * 100

# Shorten to DRC
data = data.replace({'Democratic_Republic_of_the_Congo': 'D.R.C'}, regex=True)
data = data.replace({'Falkland_Islands_(Malvinas)': 'Falklands'}, regex=True)
data = data.replace({'Democratic_Republic_of_the_Congo': 'D.R.C'}, regex=True)
data = data.replace(
    {'Cases_on_an_international_conveyance_Japan': 'Cruise Ship (Japan)'}, regex=True)
data = data.replace(
    {'Saint_Vincent_and_the_Grenadines': 'St.Vincent & the Grenadines'}, regex=True)
data = data.replace(
    {'United_States_Virgin_Islands': 'U.S Virgin Islands'}, regex=True)

data.to_csv('ECDCdata.tsv',sep='\t', mode='w', encoding = 'UTF-8')
      
access_key = ACCESS_KEY
secret_key = SECRET_KEY
            
s3_upload(access_key,secret_key, 'ECDCdata.tsv')