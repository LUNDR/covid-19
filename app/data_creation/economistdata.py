# for data managaement
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
# for scraping data
import bs4
import requests
import boto3

from config import ACCESS_KEY,SECRET_KEY



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



url = "https://github.com/TheEconomist/covid-19-excess-deaths-tracker/tree/master/output-data/excess-deaths"
res = requests.get(url)      
soup = bs4.BeautifulSoup(res.content, features="lxml")
links = [] 
for div in soup.find_all(name='a', attrs={'class':'js-navigation-open'}):
    u = 'https://github.com'+div['href']
    if '.csv' in u:
        u2 = "https://raw.githubusercontent.com/TheEconomist/covid-19-excess-deaths-tracker/master/output-data/excess-deaths/"+u.split('/')[-1]
        links.append(u2)
    else:
        pass

def end_date_from_week(n,country):
    return datetime.strptime(df[(df.country==country) & (df.week==n)]['end_date'].iloc[0],'%Y-%m-%d')
        
    
df = pd.DataFrame()
for l in links:
    temp = pd.read_csv(l)
    df = pd.concat([df,temp],axis = 0)
df.loc[df.country=='Turkey','country'] = 'Istanbul (Turkey)'

df.drop_duplicates(subset =["country","week","region"], 
                     keep = 'first', inplace = True)

df.reset_index(inplace=True, drop = True)

print(df.country.unique())
df_agg = df[df.country.isin(['Indonesia','Russia','Istanbul (Turkey)'])].groupby(['country','year','week'], as_index = False).agg({'expected_deaths':'sum','excess_deaths':'sum','covid_deaths':'sum','total_deaths':'sum','non_covid_deaths':'sum','population':['sum','count']})

maxes = dict(zip(df_agg.groupby('country').max()[('population','count')].index,df_agg.groupby('country').max()[('population','count')].values))

df_agg['flag'] = 1
temp=[]
for i in range(len(df_agg)):
    temp.append((df_agg[('population','count')][i] == maxes[df_agg.country[i]])*1)
df_agg['flag'] = temp

df_agg2 = df_agg[df_agg.flag>0].drop(columns=[('population','count'),'flag'])
df_agg2.columns = [x[0] for x in df_agg2.columns]
df_o = df[(df.country==df.region) & (df.week>0) ][[x for x in df_agg2.columns]]
df_chart = pd.concat([df_o,df_agg2])
df_chart = df_chart.reset_index()
df_chart['end_date_week'] = 0 
for i in range(len(df_chart)):
    df_chart['end_date_week'][i] = end_date_from_week(df_chart.week[i],df_chart.country[i])

df_chart['expected_deaths_per_mil'] = df_chart.expected_deaths/df_chart.population*1000000
df_chart['excess_deaths_per_mil'] = df_chart.excess_deaths/df_chart.population*1000000
df_chart['total_deaths_per_mil'] = df_chart.total_deaths/df_chart.population*1000000

url = "http://api.worldbank.org/v2/country/all/indicator/EN.POP.DNST?format=json&per_page=30000"
response = requests.get(url).json()

#pd.DataFrame.from_dict(response[1], orient ='index', columns = [names[j]])

wb = pd.DataFrame(columns=['year','ISO','density'])
#data_dict ={}
count=0
for i in response[1]:
    temp = pd.DataFrame(i)
    wb.loc[count]=[i['date'],i['countryiso3code'],i['value']]
    count+=1

wb2  = wb.dropna(axis=0)
den = wb2[wb2.groupby(by=['ISO'])['year'].transform(max)==wb2.year]



con_dict = dict(zip(df_chart['country'].unique(),['AUT','BEL','GBR','CHL','DNK','FRA','DEU','ITA','NLD','NOR','PRT','ZAF','ESP','SWE','CHE','USA','TUR']))

df_chart['ISO']= df_chart.country.map(lambda x: con_dict[x])

df_chart = pd.merge(df_chart,den[['density','ISO']],left_on='ISO',right_on='ISO',how='left')
df_chart['cumulative_excess_deaths_per_mil'] = df_chart[df_chart.week>8].groupby(by='country')['excess_deaths_per_mil'].cumsum()

df_chart.to_csv('economistdata.tsv',sep='\t', mode='w', encoding = 'UTF-8')
      
access_key = ACCESS_KEY
secret_key = SECRET_KEY
            
s3_upload(access_key,secret_key, 'economistdata.tsv')
