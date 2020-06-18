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
from palettable.colorbrewer.qualitative import Paired_12
from palettable.tableau import Tableau_20


# for dash app
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

# for scraping data
import bs4
import requests


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


# Data read in and feature creation/ data wrangling

data = pd.read_csv(
    'https://covid-19-app-data.s3.eu-west-2.amazonaws.com/ECDCdata.csv',
    usecols=list(
        range(
            0,
            11)))

continents = pd.read_csv('assets/continents.csv')

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

# Formatting
# colours

# sort values so hopefully countries with similar number of cases end up
# with different colours
a = data.sort_values(
    by=['total_cases', 'countriesAndTerritories', 'dateRep'], ascending=True)

colour_list = (Tableau_20.hex_colors *
               int(len(data['countriesAndTerritories'].unique()) /
                   len(Tableau_20.hex_colors) +
                   1))[:len(data['countriesAndTerritories'].unique())]
colour_dict = dict(
    zip(list(dict.fromkeys(a['countriesAndTerritories'])), colour_list))
data['colour'] = [colour_dict[x] for x in data['countriesAndTerritories']]

## colour list for excess deaths chart

colour_list2 = (Tableau_20.hex_colors *
               int(len(data['countryterritoryCode'].unique()) /
                   len(Tableau_20.hex_colors) +
                   1))[:len(data['countryterritoryCode'].unique())]
colour_dict2 = dict(
    zip(list(dict.fromkeys(a['countryterritoryCode'])), colour_list))




# colour dictionary for continents
colours = {"Asia": "royalblue",
           "Europe": "crimson",
           "Africa": "lightseagreen",
           "Oceania": "orange",
           "North America": "gold",
           "South America": 'mediumslateblue',
           "nan": "peru"}

#
title_font_family = 'Arial'
title_font_size = 14
x_title_font_size = 11
y_title_font_size = 11

# create a 'date' variable that is a string
data['date'] = [pd.to_datetime(str(x)).strftime('%d %b')
                for x in data['dateRep']]


# create objects to be used universally
# create a list of date strings to cycle through for animations
days = data['dateRep'][data['dateRep'] > pd.to_datetime(
    '31-12-2019')].sort_values(ascending=True).unique()
days = [pd.to_datetime(str(x)).strftime('%d %b') for x in days]

# calculate the date of latest data included and make it a string
latest_data = data['dateRep'].max()
latest_data_string = latest_data.strftime("%d %b %Y")

###################################################################

# Animated Map

figure = {
    'data': [],
    'layout': {},
    'frames': [],
    'config': {'scrollzoom': False}
}


# data

day = days[-1]
data_ = []
traces = []


chart_data = data[data['date'] == day]
for i, cont in enumerate(chart_data['Continent_Name'].unique()[:-1]):
    colour = colours[cont]
    df_sub = chart_data[chart_data['Continent_Name'] == cont].reset_index()
    data_dict = dict(
        type='scattergeo',
        locationmode='ISO-3',
        locations=df_sub['countryterritoryCode'].tolist(),
        marker=dict(
            size=df_sub['total_cases'] / 1000,
            color=colour,
            line_color='#ffffff',
            line_width=0.5,
            sizemode='area'),
        name='{}'.format(cont),
        text=[
            '{}<BR>Total Cases: {}'.format(
                ' '.join(df_sub['countriesAndTerritories'][x].split('_')),
                df_sub['total_cases'][x]) for x in range(
                    len(df_sub))])
    figure['data'].append(data_dict)


### frames & steps
frames = []
steps = []

for day in days:
    chart_data = data[data['date'] == day]
    frame = dict(data=[], name=str(day))
    for i, cont in enumerate(chart_data['Continent_Name'].unique()[:-1]):
        colour = colours[cont]
        df_sub = chart_data[chart_data['Continent_Name'] == cont].reset_index()
        data_dict = dict(
            type='scattergeo',
            locationmode='ISO-3',
            locations=df_sub['countryterritoryCode'].tolist(),
            marker=dict(
                size=df_sub['total_cases'] / 1000,
                color=colour,
                line_color='#ffffff',
                line_width=0.5,
                sizemode='area'),
            name='{}'.format(cont),
            text=[
                '{}<BR>Total Cases: {:,}'.format(
                    ' '.join(df_sub['countriesAndTerritories'][x].split('_')),
                    df_sub['total_cases'][x]) for x in range(
                    len(df_sub))])
        frame['data'].append(data_dict)
    figure['frames'].append(frame)

    step = dict(
        method="animate",
        args=[
            [day],
            dict(frame=dict(duration=100,
                            redraw=True),
                 mode="immediate",
                 transition=dict(duration=100,
                                 easing="quad-in"))
        ],
        label=day,

    )

    # append step to step list
    steps.append(step)


# Create and add aslider
sliders = [dict(
    y=0,
    active=len(days) - 1,
    currentvalue=dict(prefix="",
                      visible=True,
                      ),
    transition=dict(duration=300),
    pad=dict(t=2),
    steps=steps
)]

# layout
figure['layout'] = dict(
    titlefont=dict(
        size=title_font_size,
        family=title_font_family),
    title_text='<b> COVID-19 Total Cases </b> <BR>' + '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>',
    showlegend=True,
    geo=dict(
        scope='world',
        landcolor='rgb(217, 217, 217)',
        coastlinecolor='#ffffff',
        countrywidth=0.5,
        countrycolor='#ffffff',
    ),
    updatemenus=[
        dict(
            type='buttons',
            buttons=list(
                [
                    dict(
                        args=[
                            None,
                            dict(
                                frame=dict(
                                    duration=200,
                                    redraw=True),
                                mode="immediate",
                                transition=dict(
                                    duration=200,
                                    easing="quad-in"))],
                        label="Play",
                        method="animate")]))],
    sliders=sliders)

map1 = go.Figure(figure)

# Death rate chart

figure = {
    'data': [],
    'layout': {},
    'frames': [],
    'config': {'scrollzoom': False}
}

# choose the first date in the 'days' list as your data
day = days[-1]

# define the maximum number of countries to be shown on the graph
num_ = 204

# define the threshold for being shown
threshold = 100

# subset the data by date
chart_data = chart_data = data.loc[(data['date'] == day) & (
    data['total_cases'] > threshold)].sort_values(by='death_rate', ascending=False)

# select only the first num_ countries in the new dataframe
chart_data_2 = chart_data[0:num_]

# create a colour variable for the new dataframe, assigning each country a
# colour according to the colour dictionary
chart_data_2['colour'] = [colours[str(x)]
                          for x in chart_data_2['Continent_Name']]

# define the chart
data_dict = dict(type='bar',
                 x=[' '.join(x.split('_')) for x in chart_data_2['countriesAndTerritories']],
                 y=chart_data_2['death_rate'],
                 name='',
                 text=chart_data_2['countriesAndTerritories'].tolist(),
                 customdata=chart_data_2['total_cases'],
                 marker=dict(color=chart_data_2['colour'].tolist()),
                 hovertemplate="<br><b>%{text}</b><br> Death Rate (%): %{y:0.1f}<br>Total Cases: %{customdata:,}<extra></extra>")

figure['data'] = data_dict


# frames

# define lists to capture frames and steps in a loop
frames = []
steps = []

# loop through days making a new frame and a new step each time
for day in days:

    # create data subset, based on date, and threshold, sort values, take the
    # first num_ countries then assign colours
    chart_data = chart_data = data.loc[(data['date'] == day) & (
        data['total_cases'] > threshold)].sort_values(by='death_rate', ascending=False)
    chart_data_2 = chart_data[0:num_]
    chart_data_2['colour'] = [colours[str(x)]
                              for x in chart_data_2['Continent_Name']]

    frame = dict(data=[], name=str(day))
    # create chart
    data_dict = dict(type='bar',
                     x=[' '.join(x.split('_')) for x in chart_data_2['countriesAndTerritories']],
                     y=chart_data_2['death_rate'],
                     name='',
                     text=chart_data_2['countriesAndTerritories'].tolist(),
                     customdata=chart_data_2['total_cases'],
                     marker=dict(color=chart_data_2['colour'].tolist()),
                     hovertemplate="<br><b>%{text}</b><br> Death Rate (%): %{y:0.1f}<br>Total Cases: %{customdata:,}<extra></extra>")

    # add to chart list
    frame['data'].append(data_dict)
    figure['frames'].append(frame)

    # create steps
    step = dict(
        method="animate",
        args=[
            [day],
            dict(frame=dict(duration=100,
                            redraw=True),
                 mode="immediate",
                 transition=dict(duration=100,
                                 easing="quad-in"))
        ],
        label=day,

    )

    # append step to step list
    steps.append(step)


# Create and add aslider
sliders = [dict(
    y=-0.3,
    active=len(days) - 1,
    currentvalue=dict(prefix="Date: ",
                      visible=True),
    transition=dict(duration=300),
    pad=dict(t=50),
    steps=steps
)]

figure['layout'] = dict(
    title='<b>Ratio of total reported deaths from COVID-19 to total reported cases</b> <BR>' + '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>',
     titlefont=dict(
        size=title_font_size, family=title_font_family),
        yaxis=dict(
            title=dict(
                text="%", font=dict(
                    size=y_title_font_size))),
    sliders=sliders)


# add a footnote
footnote = dict(
    xref='paper',
    xanchor='right',
    text="Note: Differences in the scope of testing <BR>for the virus and in reporting across <BR> countries means that figures <BR> should be compared with caution; <BR> Only countries with more than 100 cases are shown",
    x=0.95,
    yanchor='bottom',
    yshift=-
    100,
    xshift=0,
    showarrow=False,
    font=dict(
        size=10),
    bgcolor="#ffffff",
    bordercolor="#D3D3D3",
    borderwidth=2,
    borderpad=4,
    y=20)

figure['layout']['annotations'] = [footnote]

fig1 = go.Figure(figure)

#################################################################################################

# deaths log chart

# choose the countries we want on the plot
countries = data['countriesAndTerritories'].unique()

# choose whether we want to plot total_cases or total_deaths
cat_ = 'deaths'  # deaths / cases
type_ = '_7_day_sum'  # '_7_day_sum' / 'total_' /''
var = cat_ + type_

# choose how many cumulative deaths/or cases to use as point 0
index_ = 10

# list the countries you want to be on there as a default
default_list = [
    'United_States_of_America',
    'Japan',
    'United_Kingdom',
    'Italy',
    'Switzerland',
    'France']

# calculate the date of latest data included and make it a string
latest_data = data['dateRep'].max()
latest_data_string = latest_data.strftime("%d %b %Y")

# define plot title and axis titles

if type_ == '_7_day_sum':
    plot_title = "<b>COVID-19 " + cat_.capitalize() + ': 7 day rolling average</b><BR>' + latest_data_string +  '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>'
elif type_ == 'total_':
    plot_title = '<b>COVID-19 ' + cat_.capitalize() + '</b> <BR> cumulative total <BR>' + latest_data_string + '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>'
else:
    plot_title = '<b>COVID-19 ' + cat_.capitalize() + '</b><BR>' + latest_data_string + '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>'


x_title = "Days since " + str(index_) + " " + cat_ + " reached</b>"
y_title = cat_.capitalize() + " (log scale)"


# Build traces to go on the plot


figure = {
    'data': [],
    'layout': {},
    'config': {'scrollzoom': False}
}

dfs = dict()
annotations = []
traces = []

for i in countries:
    try:
        if i in default_list:
            dfs[i] = reindex(make_chart_data(i), var, index_)
            data_dict = dict(type='scatter',
                             x=dfs[i].index,
                             y=dfs[i][var],
                             mode='lines',
                             line=dict(shape='hv', color=dfs[i]['colour'][0]),
                             marker=dict(),
                             line_shape='linear',
                             # Removes the underscores in the legend names for
                             # countries
                             name=' '.join(i.split('_')),
                             # Removes the underscores in the hoverlabel names
                             text=[' '.join(x.split('_'))
                                   for x in dfs[i]['countriesAndTerritories']],
                             hovertemplate="<br><b>%{text}</b><br><i> Weekly " + cat_.capitalize() + "</i>: %{y:,}<extra></extra>")  # formats the hoverlabels
            traces.append(data_dict)
        else:
            dfs[i] = reindex(make_chart_data(i), var, index_)
            data_dict = dict(type='scatter',
                             x=dfs[i].index,
                             y=dfs[i][var],
                             mode='lines',
                             line=dict(shape='hv', color=dfs[i]['colour'][0]),
                             marker=dict(),
                             line_shape='linear',
                             # Removes the underscores in the legend names for
                             # countries
                             name=' '.join(i.split('_')),
                             # Removes the underscores in the hoverlabel names
                             text=[' '.join(x.split('_'))
                                   for x in dfs[i]['countriesAndTerritories']],
                             hovertemplate="<br><b>%{text}</b><br><i> Weekly " + \
                             cat_.capitalize() + "</i>: %{y:,}<extra></extra>",
                             visible='legendonly')  # formats the hoverlabels
            traces.append(data_dict)
    except BaseException:
        pass


# create traces for the lines you want to plot (as for the other lines)

three_days = dict(type='scatter',
                  x=np.array(range(0, 90)),
                  y=index_ * (2**(1 / 3))**np.array(range(0, 90)),
                  mode='lines',
                  line=dict(color='#999999', shape='hv', dash='dot'),
                  line_shape='linear',
                  name='Doubling every three days',
                  hoverinfo='skip')

seven_days = dict(type='scatter',
                  x=np.array(range(0, 90)),
                  y=index_ * (2**(1 / 7))**np.array(range(0, 90)),
                  mode='lines',
                  line=dict(color='#999999', shape='hv', dash='dot'),
                  line_shape='linear',
                  name='Doubling every week',
                  hoverinfo='skip')

# add the lines to the list of traces to plot
traces.append(three_days)
traces.append(seven_days)

figure['data'] = traces

# add annotations to the lines so people can see what they are

annotations.append(dict(xref='paper',
                        x=0.5,
                        y=4.7,
                        text='Doubling every <BR> 3 days',
                        font=dict(family='Arial', size=10), showarrow=False))
annotations.append(dict(xref='paper',
                        x=0.93,
                        y=3.8,
                        text='Doubling every <BR> week',
                        font=dict(family='Arial', size=10), showarrow=False))


# add a footnote

#footnote = dict(xref='paper',
#                 xanchor='right',
#                 x=1,
#                yanchor='top',
#                y=np.log10(index_),
#                text='<BR> <BR> <BR> <BR> <BR>Sources: Chart by Rachel Lund (2020) https://github.com/LUNDR/covid-19; data from https://www.ecdc.europa.eu',
#               font=dict(family='Arial',size=10),showarrow=False)
#annotations.append(footnote)


figure['layout'] = dict(
    yaxis_type="log", title=plot_title, annotations=annotations, titlefont=dict(
        size=title_font_size, family=title_font_family), xaxis=dict(
            title=dict(
                text=x_title, font=dict(
                    size=x_title_font_size)), range=[
                        0, 120]), yaxis=dict(
                            title=dict(
                                text=x_title, font=dict(
                                    size=x_title_font_size)), range=[
                                        0, 5]))


fig2 = go.Figure(figure)

# log chart cases

# choose whether we want to plot total_cases or total_deaths
cat_ = 'cases'  # deaths / cases
type_ = '_7_day_sum'  # '_7_day_sum' / 'total_' /''
var = cat_ + type_

# choose how many cumulative deaths/or cases to use as point 0
index_ = 100

# list the countries you want to be on there as a default
default_list = [
    'United_States_of_America',
    'Japan',
    'United_Kingdom',
    'Italy',
    'Switzerland',
    'France']

# calculate the date of latest data included and make it a string
latest_data = data['dateRep'].max()
latest_data_string = latest_data.strftime("%d %b %Y")

# define plot title and axis titles

if type_ == '_7_day_sum':
    plot_title = "<b>COVID-19 " + \
        cat_.capitalize() + ": 7 day rolling average</b><BR>" + latest_data_string  + '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>'
elif type_ == 'total_':
    plot_title = "<b>COVID-19 " + \
        cat_.capitalize() + "</b> <BR> cumulative total <BR>" + latest_data_string  + '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>'
else:
    plot_title = "<b>COVID-19 " + cat_.capitalize() + "</b><BR>" + \
        latest_data_string  + '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>'


x_title = "Days since " + str(index_) + " " + cat_ + " reached</b>"
y_title = cat_.capitalize() + " (log scale)"

# Build traces to go on the plot


figure = {
    'data': [],
    'layout': {},
    'config': {'scrollzoom': False}
}

dfs = dict()
annotations = []
traces = []

for i in countries:
    try:
        if i in default_list:
            dfs[i] = reindex(make_chart_data(i), var, index_)
            data_dict = dict(type='scatter',
                             x=dfs[i].index,
                             y=dfs[i][var],
                             mode='lines',
                             line=dict(shape='hv', color=dfs[i]['colour'][0]),
                             marker=dict(),
                             line_shape='linear',
                             # Removes the underscores in the legend names for
                             # countries
                             name=' '.join(i.split('_')),
                             # Removes the underscores in the hoverlabel names
                             text=[' '.join(x.split('_'))
                                   for x in dfs[i]['countriesAndTerritories']],
                             hovertemplate="<br><b>%{text}</b><br><i> Weekly " + cat_.capitalize() + "</i>: %{y:,}<extra></extra>")  # formats the hoverlabels
            traces.append(data_dict)
        else:
            dfs[i] = reindex(make_chart_data(i), var, index_)
            data_dict = dict(type='scatter',
                             x=dfs[i].index,
                             y=dfs[i][var],
                             mode='lines',
                             line=dict(shape='hv', color=dfs[i]['colour'][0]),
                             marker=dict(),
                             line_shape='linear',
                             # Removes the underscores in the legend names for
                             # countries
                             name=' '.join(i.split('_')),
                             # Removes the underscores in the hoverlabel names
                             text=[' '.join(x.split('_'))
                                   for x in dfs[i]['countriesAndTerritories']],
                             hovertemplate="<br><b>%{text}</b><br><i> Weekly " + \
                             cat_.capitalize() + "</i>: %{y:,}<extra></extra>",
                             visible='legendonly')  # formats the hoverlabels
            traces.append(data_dict)
    except BaseException:
        pass


# create traces for the lines you want to plot (as for the other lines)

three_days = dict(type='scatter',
                  x=np.array(range(0, 90)),
                  y=index_ * (2**(1 / 3))**np.array(range(0, 90)),
                  mode='lines',
                  line=dict(color='#999999', shape='hv', dash='dot'),
                  line_shape='linear',
                  name='Doubling every three days',
                  hoverinfo='skip')

seven_days = dict(type='scatter',
                  x=np.array(range(0, 90)),
                  y=index_ * (2**(1 / 7))**np.array(range(0, 90)),
                  mode='lines',
                  line=dict(color='#999999', shape='hv', dash='dot'),
                  line_shape='linear',
                  name='Doubling every week',
                  hoverinfo='skip')

# add the lines to the list of traces to plot
traces.append(three_days)
traces.append(seven_days)

figure['data'] = traces

# add annotations to the lines so people can see what they are

annotations.append(dict(xref='paper',
                        x=0.5,
                        y=5.7,
                        text='Doubling every <BR> 3 days',
                        font=dict(family='Arial', size=10), showarrow=False))
annotations.append(dict(xref='paper',
                        x=0.93,
                        y=4.8,
                        text='Doubling every <BR> week',
                        font=dict(family='Arial', size=10), showarrow=False))


# add a footnote

# footnote = dict(xref='paper',
#                 xanchor='right',
#                 x=1,
#                 yanchor='top',
#                 y=np.log10(index_),
#                 text='<BR> <BR> <BR> <BR> <BR>Sources: Chart by Rachel Lund (2020) https://github.com/LUNDR/covid-19; data from https://www.ecdc.europa.eu',
#                 font=dict(family='Arial',size=10),showarrow=False)
# annotations.append(footnote)


figure['layout'] = dict(
    yaxis_type="log", title=plot_title, annotations=annotations, titlefont=dict(
        size=title_font_size, family=title_font_family), xaxis=dict(
            title=dict(
                text=x_title, font=dict(
                    size=x_title_font_size)), range=[
                        0, 130]), yaxis=dict(
                            title=dict(
                                text=x_title, font=dict(
                                    size=x_title_font_size)), range=[
                                        0, 6]))


fig3 = go.Figure(figure)
# bubble scatter chart

# bubble scatter chart

countries = data['countriesAndTerritories'].unique()

# define titles
x_title = 'Cases per 100,000 population'
y_title = 'Deaths per 100,000 population'
plot_title = '<b>Total cases of Covid-19 v Total deaths : per 100,000 population</b><BR>' + latest_data_string  + '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>'

# what to show to start
default_list = [
    'United_States_of_America',
    'France',
    'Netherlands',
    'United_Kingdom',
    'Italy',
    'Switzerland',
    'Germany',
    'South_Korea',
    'Spain']

# size reference for bubbles
sizeref = 2. * max(data['popData2018']) / (150 ** 2)


figure = {
    'data': [],
    'layout': {},
    'config': {'scrollzoom': False}
}

traces = []

for i in countries:
    try:
        chart_data = data.loc[(data['dateRep'] == max(data['dateRep'])) & (
            data['countriesAndTerritories'] == i)]
        if np.isnan(chart_data['popData2018'].tolist()[0]):
            pass
        elif i in default_list:
            data_dict = dict(
                type='scatter',
                x=list(
                    chart_data['cases_per_cap'] *
                    100000),
                y=list(
                    chart_data['deaths_per_cap'] *
                    100000),
                text=[
                    ' '.join(
                        x.split('_')) for x in chart_data['countriesAndTerritories']],
                marker=dict(
                    color=chart_data['colour'],
                    size=chart_data['popData2018'],
                    sizeref=sizeref,
                    sizemode='area',
                    line=dict(
                        color='#ffffff')),
                mode='markers',
                customdata=chart_data['popData2018'] /
                1000000,
                hovertemplate="<br><b>%{text}</b><br>Cases per 100k people: %{x:0.1f}<BR> Deaths per 100k people: %{y:0.1f}<BR> Population (2018) %{customdata:,.0f}M<extra></extra>",
                name=' '.join(
                    i.split('_')))
            traces.append(data_dict)
        else:
            data_dict = dict(
                type='scatter',
                x=list(
                    chart_data['cases_per_cap'] *
                    100000),
                y=list(
                    chart_data['deaths_per_cap'] *
                    100000),
                text=[
                    ' '.join(
                        x.split('_')) for x in chart_data['countriesAndTerritories']],
                marker=dict(
                    color=chart_data['colour'],
                    size=chart_data['popData2018'],
                    sizeref=sizeref,
                    sizemode='area',
                    line=dict(
                        color='#ffffff')),
                mode='markers',
                customdata=chart_data['popData2018'] /
                1000000,
                hovertemplate="<br><b>%{text}</b><br>Cases per 100k people: %{x:0.1f}<BR> Deaths per 100k people: %{y:0.1f}<BR> Population (2018) %{customdata:,.0f}M<extra></extra>",
                name=' '.join(
                    i.split('_')),
                visible='legendonly')
            traces.append(data_dict)

    except BaseException:
        pass

figure['data'] = traces
figure['layout'] = dict(
    title=plot_title, titlefont=dict(
        size=title_font_size, family=title_font_family), xaxis=dict(
            title=dict(
                text=x_title, font=dict(
                    size=x_title_font_size)), range=[
                        0, 700], ), yaxis=dict(
                            title=dict(
                                text=y_title, font=dict(
                                    size=y_title_font_size)), range=[
                                        0, 70]))


fig4 = go.Figure(figure)

# headline chart

figure = {
    'data': [],
    'layout': {},
    'config': {'scrollzoom': False}
}

traces = []
names = [
    'Total Cases',
    'Total Deaths',
    'Latest Daily Cases',
    'Latest Daily Deaths']



for country in data['countriesAndTerritories'].unique():
    customdata = [country,country,country,country]
    colour = data[data['countriesAndTerritories'] == country]['colour'].tolist()[
        0]
    chart_data = data[(data['dateRep'] == data['dateRep'].max()) & (
        data['countriesAndTerritories'] == country)][['total_cases', 'total_deaths', 'cases', 'deaths']].T
    try:
        if country == 'World':
            data_dict = dict(type='bar',
                             y=names,
                             x=chart_data.iloc[:, 0],
                             customdata = customdata,
                             name=' '.join(country.split('_')),
                             text=['<b>{}</b>: {:,}'.format(z, x) for x, z in zip(chart_data.iloc[:, 0], customdata)],
                             textposition=['inside', 'outside', 'outside', 'outside'],
                             marker=dict(color='firebrick'),
                             hovertemplate = "<br><b>%{customdata}</b><br>%{y}: %{x:,}<extra></extra>",
                             orientation='h',
                             )
            traces.append(data_dict)
            
        else:
            data_dict = dict(type='bar',
                             y=names,
                             x=chart_data.iloc[:, 0],
                             customdata = [country,country,country,country],
                             name=' '.join(country.split('_')),
                             text=['<b>{}</b>: {:,}'.format(' '.join(z.split('_')), x) for x, z in zip(chart_data.iloc[:, 0], customdata)],
                             textposition=['outside', 'outside', 'outside', 'outside'],
                             marker=dict(color=colour),
                             orientation='h',
                             visible='legendonly',
                             hovertemplate = "<br><b>%{customdata}</b><br>%{y}:%{x:,}<extra></extra>",
                             )
            traces.append(data_dict)
    except BaseException:
        pass

figure['data'] = traces
figure['layout'] = dict(
    yaxis=dict(
        autorange="reversed"),
    title='<b>Headline Figures: COVID-19 Cases and Deaths</b> <BR>' + latest_data_string  + '<br><span style="font-size: 11px;">Source: European Centre for Disease Prevention and Control</span>',
    titlefont=dict(
        size=title_font_size,
        family=title_font_family))

headline = go.Figure(figure)

###### excess deaths


df_chart = pd.read_csv('https://covid-19-app-data.s3.eu-west-2.amazonaws.com/economistdata.tsv', sep ='\t')
df_chart['expected_deaths_per_mil'] = df_chart.expected_deaths/df_chart.population*1000000
df_chart['excess_deaths_per_mil'] = df_chart.excess_deaths/df_chart.population*1000000
df_chart['total_deaths_per_mil'] = df_chart.total_deaths/df_chart.population*1000000

df_chart['colour'] = [colour_dict2[x] for x in df_chart['ISO']]


figure = {
    'data': [],
    'config': {'scrollzoom': True}
}

visible_0 = []
visible_1 = []

for i in ['Britain']:
    for j,k in enumerate(['expected_deaths','total_deaths','excess_deaths']):
        data_dict = dict(mode='lines',
                     x = df_chart[df_chart.country == i].end_date_week,
                     y = [int(n) for n in df_chart[df_chart.country == i][k]],
                    line=dict(
                    width=1.5
                    ),
                name = '{}: {}'.format(i,' '.join(k.split('_')).capitalize()),
                text = [],
                visible=False,
                hovertemplate = "<br><b>{}</b><br><i>{}".format(i,' '.join(k.split('_')).capitalize())+"</i>: %{y:,}<br>Week Ending: %{x}<extra></extra>")
               
        figure['data'].append(data_dict)
        visible_0.append(True)
        visible_1.append(False)


for i in ['Britain']:
    for j,k in enumerate(['expected_deaths_per_mil','total_deaths_per_mil','excess_deaths_per_mil']):
        data_dict = dict(mode='lines',
                     x = df_chart[df_chart.country == i].end_date_week,
                     y = [int(n) for n in df_chart[df_chart.country == i][k]],
                    line=dict(
                    width=1.5
                    ),
                name = '{}: {}'.format(i,' '.join(k.split('_')).capitalize()),
                text = [],
                visible = True,
                hovertemplate = "<br><b>{}</b><br><i>{}".format(i,' '.join(k.split('_')).capitalize())+"</i>: %{y:,}<br>Week Ending: %{x}<extra></extra>")
               
        figure['data'].append(data_dict)
        visible_0.append(False)
        visible_1.append(True)
        
        
cou =[x for x in df_chart.country.unique()]
cou.remove('Britain')
for i in cou:
    for j,k in enumerate(['expected_deaths','total_deaths','excess_deaths']):
        data_dict = dict(mode='lines',
                     x = df_chart[df_chart.country == i].end_date_week,
                     y = [int(n) for n in df_chart[df_chart.country == i][k]],
                    line=dict(
                    width=1.5
                    ),
                name = '{}: {}'.format(i,' '.join(k.split('_')).capitalize()),
                text = [],
                visible = False,
                hovertemplate = "<br><b>{}</b><br><i>{}".format(i,' '.join(k.split('_')).capitalize())+"</i>: %{y:,}<br>Week Ending:  %{x}<extra></extra>")
               
        figure['data'].append(data_dict)
        visible_0.append('legendonly')
        visible_1.append(False)
            
for i in cou:
    for j,k in enumerate(['expected_deaths_per_mil','total_deaths_per_mil','excess_deaths_per_mil']):
        data_dict = dict(mode='lines',
                     x = df_chart[df_chart.country == i].end_date_week,
                     y = [int(n) for n in df_chart[df_chart.country == i][k]],
                    line=dict(
                    width=1.5
                    ),
                name = '{}: {}'.format(i,' '.join(k.split('_')).capitalize()),
                text = [],
                visible = 'legendonly',
                hovertemplate = "<br><b>{}</b><br><i>{}".format(i,' '.join(k.split('_')).capitalize())+"</i>: %{y:,}<br>Week Ending:  %{x}<extra></extra>")
               
        figure['data'].append(data_dict)
        visible_0.append(False)
        visible_1.append('legendonly')            
####    
figure['layout'] = dict(
    margin= dict( t=150),

    title = dict(yanchor = 'top', pad = dict(b = 200, t=200)),
    titlefont=dict(
        size=title_font_size,
        family=title_font_family),
    hovermode = 'x',
    title_text='<b>Weekly Expected Deaths, Total Deaths & Excess Deaths </b><br><span style="font-size: 12px;">Source:The Economist</span><br><span style="font-size: 12px;"><i>Expected deaths are calculated as an average of 2015/16-2019, except for Spain and South Africa,<br> which are independently modelled </i> ',
    showlegend=True,
    yaxis=dict(
            title=dict(
                text="Weekly Deaths", font=dict(
                    size=y_title_font_size))),
    xaxis=dict(
            title=dict(
                text="Week Ending", font=dict(
                    size=y_title_font_size))),
    
    updatemenus = list([
    dict(active=1,
         showactive = False,
         buttons=list([   
            dict(label = "Raw Numbers",
                 method = "update",
                 args = [{"visible": visible_0}]), # hide trace2
            dict(label = "Per million people",
                 method = "update",
                 args = [{"visible": visible_1}]) # hide trace1
            ]),
         direction="down",
            pad={"r": 10, "t": 10},
            x=1.55,
            xanchor="right",
            y=1.2,
            yanchor="top"
        
        )])

)




fig5 = go.Figure(figure)

### excess deaths v pop density

week = 19
from sklearn.linear_model import LinearRegression
X = np.array(df_chart[df_chart.week==week]['density']).reshape(-1,1)
y=df_chart[df_chart.week==week]['cumulative_excess_deaths_per_mil']
reg=LinearRegression().fit(X, y)
y_pred=reg.predict(X)
r2 = r2_score(y,y_pred)

countries = [x for x in list(df_chart['country'].unique()) if x not in ['Istanbul (Turkey)']]


data_shown = 'First week of March up to week ending '+df_chart[df_chart.week==week].iloc[0]['end_date_week'].strftime("%d-%b")

# define titles
x_title = 'density(pop per sq.km)'
y_title = 'excess deaths per million people.'
plot_title = '<b>Cumulative excess deaths v population density </b><BR>' + data_shown + '<br><span style="font-size: 11px;">Source: World Bank and the Economist</span>'


default_list=countries

# size reference for bubbles

figure = {
    'data': [],
    'layout': {},
    'config': {'scrollzoom': False}
}

traces = []


for i in countries:
    try:
        chart_data = df_chart.loc[df_chart['country'] == i]
        chart_data = chart_data[chart_data['week']==week]
#         if np.isnan(chart_data['popData2018'].tolist()[0]):
#             pass
        if i in default_list:
            data_dict = dict(
                type='scatter',
                x=list(
                    chart_data['density']),
                y=list(
                    chart_data['cumulative_excess_deaths_per_mil']),
                text=[
                    ' '.join(
                        x.split('_')) for x in chart_data['country']],
                marker=dict(
                    color=chart_data['colour'],
                    size=20,
                    #sizeref=sizeref,
                    sizemode='area',
                    line=dict(
                        color='#ffffff')),
                mode='markers',
                #customdata=chart_data['popData2018'] /
                #1000000,
                hovertemplate="<br><b>%{text}</b><br>Excess Deaths per million: %{y:0.0f}<extra></extra>",
                name=' '.join(
                    i.split('_')))
            traces.append(data_dict)
        else:
            data_dict = dict(
                type='scatter',
                x=list(
                    chart_data['density']),
                y=list(
                    chart_data['cumulative_excess_deaths_per_mil']),
                text=[
                    ' '.join(
                        x.split('_')) for x in chart_data['country']],
                marker=dict(
                    color=chart_data['colour'],
                    size=20,
                    #sizeref=sizeref,
                    sizemode='area',
                    line=dict(
                        color='#ffffff')),
                mode='markers',
                #customdata=chart_data['popData2018'] /
                #1000000,
                hovertemplate="<br><b>%{text}</b><br>Excess Deaths per million: %{y:0.0f}<extra></extra>",
                name=' '.join(
                    i.split('_')))
            traces.append(data_dict)

    except BaseException:
        pass
    
reg_line = dict(type='scatter',
                  x=df_chart[df_chart.week==week]['density'],
                  y=y_pred,
                  mode='lines',
                  line=dict(color='#999999', shape='hv', dash='dot'),
                  line_shape='linear',
                  name='regression line',
                  hovertemplate="<br><b>linear regression line</b>"+"<br>Increase in excess deaths per million for each additional person per sq.km: {:0.2f}<br> R-sq: {:0.2f}<extra></extra>".format(reg.coef_[0],r2))

traces.append(reg_line)

figure['data'] = traces
figure['layout'] = dict(
    title=plot_title, titlefont=dict(
        size=title_font_size, family=title_font_family), xaxis=dict(
            title=dict(
                text=x_title, font=dict(
                    size=x_title_font_size)) ),
                    yaxis=dict(
                            title=dict(
                                text=y_title, font=dict(
                                    size=y_title_font_size)), 
                                    #range=[
                                     #   0, 70]
    ))


fig6 = go.Figure(figure)

