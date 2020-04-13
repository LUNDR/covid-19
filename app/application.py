# for data managaement
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta

# for charting
import plotly
import plotly.graph_objects as go

#colours
from palettable.colorbrewer.qualitative import Paired_12
from palettable.tableau import Tableau_20


# for dash app
import dash
import dash_core_components as dcc
import dash_html_components as html

# define functions

def make_chart_data(country):
    ''' makes a seperate dataset for a country
        takes country name as input '''
    chart_data = data.loc[data['countriesAndTerritories'] == country].reset_index()
    return chart_data

# shifts the data to 'day 0 of the corona virus'
def reindex(df, var, index_ = 10):
    ''' creates a data series which shifts data so that the day 
    where the criteria index_ is reached is at index 0
    Note cases are indexed to weekly total, while deaths to cumulative total'''
    dta = df.copy()
    
    # First we need to identify the day at which the minimum number of cases/deaths is reached
    # some countries have no data so the try/except allows the function to ignore them
    try: 
        first_day = dta[dta[var]>index_ ].index[0]

    # The cumulative cases/deaths data are then shifted back so that the first day index_ is exceeded becomes index 0
        dta[var] = dta[var].shift(-first_day)
    except:
        dta[var] = np.nan
    return dta 


# Data read in and feature creation/ data wrangling

data = pd.read_csv('https://opendata.ecdc.europa.eu/covid19/casedistribution/csv',usecols = list(range(0,10)))

continents = pd.read_csv('assets/continents.csv')

# make datetime
data['dateRep'] = pd.to_datetime(data['dateRep'], dayfirst=True)

#sort values by country and date
data.sort_values(by=['countriesAndTerritories','dateRep'], ascending = True, inplace = True)

#reindex the data now its sorted to prevent errors when creating aggregates
data = data.reindex()

# create a global aggregate figure for cases and deaths
world = data[['dateRep','cases','deaths','popData2018']].groupby(by='dateRep').sum()

world['day'] = world.index.day
world['month'] = world.index.month
world['year'] = world.index.year
world['dateRep'] = world.index
world['countriesAndTerritories'] = 'World'
world['geoId'] = 'WD'
world['countryterritoryCode']  = 'WLD'
data = pd.concat([data, world], ignore_index=True)

# Create a continents var

data = pd.merge(data, continents[['Continent_Name','Three_Letter_Country_Code']].drop_duplicates('Three_Letter_Country_Code'), how='left', left_on='countryterritoryCode', right_on='Three_Letter_Country_Code')
#create cumulative sum of deaths and cases by country and death rate
data['total_cases'] = data.groupby(by='countriesAndTerritories')['cases'].cumsum()
data['total_deaths'] = data.groupby(by='countriesAndTerritories')['deaths'].cumsum()

# create 7 day rolling average of deaths and cases


data['deaths_7_day_sum'] = data.groupby(by=['countriesAndTerritories'])['deaths'].rolling(7).sum().values
data['cases_7_day_sum'] = data.groupby(by=['countriesAndTerritories'])['cases'].rolling(7).sum().values
data['death_rate'] = data['total_deaths']/data['total_cases']*100

# Create cumulative deaths and cases per capita
data['deaths_per_cap'] = data['total_deaths']/data['popData2018']
data['cases_per_cap'] = data['total_cases']/data['popData2018']

# create death rates variable
data['death_rate'] = data['total_deaths']/data['total_cases']*100

#Shorten to DRC
data = data.replace({'Democratic_Republic_of_the_Congo':'D.R.C'}, regex=True)


# Formatting
## colours

# sort values so hopefully countries with similar number of cases end up with different colours
a = data.sort_values(by=['total_cases','countriesAndTerritories','dateRep'],ascending = True)

colour_list = (Tableau_20.hex_colors*int(len(data['countriesAndTerritories'].unique())/len(Tableau_20.hex_colors)+1))[:len(data['countriesAndTerritories'].unique())]
colour_dict = dict(zip(list(dict.fromkeys(a['countriesAndTerritories'])),colour_list))
data['colour'] = [colour_dict[x] for x in data['countriesAndTerritories']]

# colour dictionary for continents
colours = {'Asia':"royalblue", 'Europe':"crimson", 'Africa':"lightseagreen", 'Oceania':"orange", 'North America':"gold",
       'South America':'mediumslateblue', "nan":"peru"}

#
title_font_family = 'Arial'
title_font_size = 14
x_title_font_size = 11
y_title_font_size = 11

# create a 'date' variable that is a string
data['date'] = [pd.to_datetime(str(x)).strftime('%d %b') for x in data['dateRep']]


#create objects to be used universally
# create a list of date strings to cycle through for animations
days = data['dateRep'][data['dateRep'] > pd.to_datetime('15-02-2020')].sort_values(ascending=True).unique()
days = [pd.to_datetime(str(x)).strftime('%d %b') for x in days]

# calculate the date of latest data included and make it a string
latest_data = data['dateRep'].max()
latest_data_string = latest_data.strftime("%d %b %Y")

#######################

#Animated Map


figure = {
    'data': [],
    'layout': {},
    'frames': [],
    'config': {'scrollzoom': True}
}


### data

data_ = []
traces = []

day = days[-1]
chart_data = data[data['date'] == day]
for i, cont in enumerate(chart_data['Continent_Name'].unique()[:-1]):
    colour = colours[cont]
    df_sub = chart_data[chart_data['Continent_Name'] == cont].reset_index()
    data_dict ={'type':'scattergeo',
                'locationmode':'ISO-3',
                'locations' :df_sub['countryterritoryCode'].tolist(),
                'marker' : dict(
                            size = df_sub['total_cases']/200,
                            color = colour,
                            line_color= '#ffffff',
                            line_width=0.5,
                            sizemode = 'area'
                            ),
                'name' :'{}'.format(cont),
                'text' :['{}<BR>Total Cases: {}'.format(df_sub['countriesAndTerritories'][x],df_sub['total_cases'][x]) for x in range(len(df_sub))]
               }
    figure['data'].append(data_dict)


## frames
frames = []

steps = []
for day in days:
    chart_data = data[data['date'] == day]
    frame = {'data': [], 'name': str(day)}
    for i, cont in enumerate(chart_data['Continent_Name'].unique()[:-1]):
        colour = colours[cont]
        df_sub = chart_data[chart_data['Continent_Name'] == cont].reset_index()
        data_dict ={'type':'scattergeo',
                'locationmode':'ISO-3',
                'locations' :df_sub['countryterritoryCode'].tolist(),
                'marker' : dict(
                size = df_sub['total_cases']/200,
                color = colour,
                line_color= '#ffffff',
                line_width=0.5,
                sizemode = 'area'
                ),
                'name' :'{}'.format(cont),
                'text' :['{}<BR>Total Cases: {}'.format(df_sub['countriesAndTerritories'][x],df_sub['total_cases'][x]) for x in range(len(df_sub))]}
        frame['data'].append(data_dict)
    figure['frames'].append(frame)
    
    step = dict(
        method="animate",
        args=[
        [day],
        {"frame": {"duration": 100,
                   "redraw": True},
         "mode": "immediate",
         "transition": {"duration": 100,
                        "easing": "quad-in"}}
    ],
        label = day,
        
    )
    
    # append step to step list
    steps.append(step)
    


# Create and add aslider
sliders = [dict(   
    y = 0,
    active=len(days)-1,
    currentvalue={"prefix": "Date: ",
                  "visible" :True},
    transition = {"duration": 300},
    pad={"t": 50},
    steps=steps
)]

### layout
figure['layout'] = {
                    'titlefont' :{
                        "size": title_font_size
                    },
                    'title_text':'<b> Covid-19 cases </b> <BR> As reported at ' + latest_data_string,
                    'showlegend': True,
                    'geo' : dict(
                        scope = 'world',
                        landcolor = 'rgb(217, 217, 217)',
                        coastlinecolor = '#ffffff',
                        countrywidth = 0.5,
                        countrycolor = '#ffffff',
                   
                    ),
                    'updatemenus' :[dict(type ='buttons',
                                        buttons=list([
                                            dict(
                                                args=[None,{"frame": {"duration": 200,
                                                                      "redraw": True},
                                                            "mode": "immediate", 
                                                            "transition": {"duration": 200,
                                                                           "easing": "quad-in"}}],
                                                label="Play",
                                                method="animate"
                                            )
                                        ]
                                        ))],
                    'sliders':sliders
                   }
      
map1 = go.Figure(figure)

# Death rate chart
# choose the first date in the 'days' list as your data
day = days[-1]

# define the maximum number of countries to be shown on the graph
num_ = 204

# define the threshold for being shown
threshold = 100

#subset the data by date
chart_data = chart_data = data.loc[(data['date'] == day) & (data['total_cases'] > threshold)].sort_values(by = 'death_rate', ascending = False)

# select only the first num_ countries in the new dataframe
chart_data_2 = chart_data[0:num_]

# create a colour variable for the new dataframe, assigning each country a colour according to the colour dictionary
chart_data_2['colour'] = [colours[str(x)] for x in chart_data_2['Continent_Name']]

# define the chart
data_ = [go.Bar(x = [' '.join(x.split('_')) for x in chart_data_2['countriesAndTerritories']],
                y=chart_data_2['death_rate'],
                name = '',
                 text = chart_data_2['countriesAndTerritories'].tolist(),
                customdata=chart_data_2['total_cases'],
#                 textposition='auto',
                marker=dict(color=chart_data_2['colour'].tolist()),
               hovertemplate = "<br><b>%{text}</b><br> Death Rate (%): %{y:0.1f}<br>Total Cases: %{customdata:,}<extra></extra>")]


### layout
    
layout = go.Layout(
  
    title = "<b>Ratio of total reported deaths from COVID-19 to total reported cases (%)</b>",
     font=dict(
               family="Arial",
                size=11

            ))

### frames 

# define lists to capture frames and steps in a loop
frames = []
steps = []

# loop through days making a new frame and a new step each time
for day in days:
    # create data subset, based on date, and threshold, sort values, take the first num_ countries then assign colours
    chart_data = chart_data = data.loc[(data['date'] == day) & (data['total_cases'] > threshold)].sort_values(by = 'death_rate', ascending = False)
    chart_data_2 = chart_data[0:num_]
    chart_data_2['colour'] = [colours[str(x)] for x in chart_data_2['Continent_Name']]
    
    # create chart 
    frame = go.Frame(name = day, 
                     data =[ go.Bar(x = [' '.join(x.split('_')) for x in chart_data_2['countriesAndTerritories']],
                                                y=chart_data_2['death_rate'],
                                                name = '',
                                                 text = chart_data_2['countriesAndTerritories'].tolist(),
                                            customdata=chart_data_2['total_deaths'],
#                                                 textposition='auto',
                                                marker=dict(color=chart_data_2['colour'].tolist()),
                                                hovertemplate = "<br><b>%{text}</b><br> Death Rate (%): %{y:0.1f}<br>Total Cases: %{customdata:,}<extra></extra>")]
                                               )
    # add to chart list    
    frames.append(frame)  
    
    # create steps
    step = dict(
        method="animate",
        args=[
        [day],
        {"frame": {"duration": 100,
                   "redraw": True},
         "mode": "immediate",
         "transition": {"duration": 100,
                        "easing": "quad-in"}}
    ],
        label = day,
        
    )
    
    # append step to step list
    steps.append(step)



# Create and add aslider
sliders = [dict(   
    y = -0.3,
    active=len(days)-1,
    currentvalue={"prefix": "Date: ",
                  "visible" :True},
    transition = {"duration": 300},
    pad={"t": 50},
    steps=steps
)]

# append slider information to layout.
layout['sliders'] = sliders

#add a footnote
footnote = dict(xref='paper', 
                xanchor='right',
                text = "Note: Differences in the scope of testing <BR>for the virus and in reporting across <BR> countries means that figures <BR> should be compared with caution; <BR> Only countries with more than 100 cases are shown",
                x=0.95, 
                yanchor='bottom',
                yshift = -100,
                xshift = 0,
                showarrow=False,
                 font=dict(
             #   family="Ariel",
                size=10

            ),
                bgcolor="#ffffff",
                bordercolor="#D3D3D3",
                borderwidth=2,
                borderpad=4,
                y=20)

layout['annotations'] = [footnote]

# make the chart
fig1 = go.Figure(data_,layout,frames)

#fix the axes
fig1.layout.yaxis.update(range=[0,
                              20],title = 'Ratio (%)')


### deaths log chart

# choose the countries we want on the plot
countries = data['countriesAndTerritories'].unique()

# choose whether we want to plot total_cases or total_deaths
cat_ = 'deaths' # deaths / cases
type_ = '_7_day_sum' # '_7_day_sum' / 'total_' /''
var = cat_+type_

# choose how many cumulative deaths/or cases to use as point 0
index_ = 10

# list the countries you want to be on there as a default
default_list = ['United_States_of_America','Japan','United_Kingdom','Italy','Switzerland','China']

# calculate the date of latest data included and make it a string
latest_data = data['dateRep'].max()
latest_data_string = latest_data.strftime("%d %b %Y")

# define plot title and axis titles

if type_ == '_7_day_sum':
    plot_title = "<b>COVID-19 "+cat_.capitalize()+": 7 day rolling average</b><BR>"+latest_data_string
elif type_ == 'total_':
    plot_title = "<b>COVID-19 "+cat_.capitalize()+"</b> <BR> cumulative total <BR>"+latest_data_string
else:
     plot_title = "<b>COVID-19 "+cat_.capitalize()+"</b><BR>"+latest_data_string

    
x_title = "Days since "+str(index_)+" "+cat_+" reached</b>"
y_title = cat_.capitalize() + " (log scale)"
    

# Build traces to go on the plot

dfs = dict()
traces = dict()
plots = []
annotations = []


for i in countries:
    try:
        if i in default_list:
            dfs[i] = reindex(make_chart_data(i),var,index_)
            traces[i] = go.Scatter(x=dfs[i].index,
                                   y=dfs[i][var],
                                   mode = 'lines', 
                                   line = dict(shape ='hv',color = dfs[i]['colour'][0]),
                                   marker = dict(), 
                                   line_shape = 'linear',
                                   name = ' '.join(i.split('_')), # Removes the underscores in the legend names for countries
                                   text = [' '.join(x.split('_')) for x in dfs[i]['countriesAndTerritories']], # Removes the underscores in the hoverlabel names
                                   hovertemplate = "<br><b>%{text}</b><br><i> Weekly "+cat_.capitalize()+"</i>: %{y:,}<extra></extra>") # formats the hoverlabels
            plots.append(traces[i])
        else:
            dfs[i] = reindex(make_chart_data(i),var,index_)
            traces[i] = go.Scatter(x=dfs[i].index,
                                   y=dfs[i][var],
                                   mode = 'lines',
                                   line = dict(shape ='hv',color = dfs[i]['colour'][0]),marker = dict(),
                                   line_shape = 'linear',
                                   name = ' '.join(i.split('_')), 
                                   visible = 'legendonly',
                                   text = [' '.join(x.split('_')) for x in dfs[i]['countriesAndTerritories']],
                                   hovertemplate = "<br><b>%{text}</b><br><i> Weekly "+cat_.capitalize()+"</i>: %{y:,}<extra></extra>")
            plots.append(traces[i])
            
    except:
        pass
    


# create traces for the lines you want to plot (as for the other lines)
    
three_days = go.Scatter(x=np.array(range(0,90)),
                        y=index_*(2**(1/3))**np.array(range(0,90)), 
                        mode = 'lines', 
                        line = dict(color='#999999', shape ='hv', dash='dot'),
                        line_shape = 'linear', 
                        name = 'Doubling every three days',
                        hoverinfo='skip')

seven_days = go.Scatter(x=np.array(range(0,90)),
                        y=index_*(2**(1/7))**np.array(range(0,90)),
                        mode = 'lines',
                        line = dict(color='#999999',shape ='hv',dash='dot'),
                        line_shape = 'linear', 
                        name = 'Doubling every week',
                        hoverinfo='skip')

# add the lines to the list of traces to plot
plots.append(three_days)
plots.append(seven_days)

# add annotations to the lines so people can see what they are

annotations.append(dict(xref='paper',
                        x=0.5, 
                        y=4.7,
                        text='Doubling every <BR> 3 days',
                        font=dict(family='Arial',size=10),showarrow=False))
annotations.append(dict(xref='paper',
                        x=0.93,
                        y=3.8,
                        text='Doubling every <BR> week',
                        font=dict(family='Arial',size=10),showarrow=False))
    

# add a footnote

#footnote = dict(xref='paper', xanchor='right', x=1, yanchor='top',y=np.log10(index_),text='<BR> <BR> <BR> <BR> <BR>Sources: Chart by Rachel Lund (2020) https://github.com/LUNDR/covid-19; data from https://www.ecdc.europa.eu',font=dict(family='Arial',size=10),showarrow=False)
#annotations.append(footnote)
  
    
fig2 = go.Figure(plots)
fig2.update_layout(yaxis_type="log",

                  title=plot_title,
                  annotations = annotations,
                 titlefont ={
                            "size": title_font_size
                  })

fig2.layout.xaxis.update(title={'text':x_title,'font':{'size':x_title_font_size}},
                        range=[0, 90], 
                        )
fig2.layout.yaxis.update(title={'text':y_title,'font':{'size':y_title_font_size}},
                        range=[np.log10(index_), 5])


# log chart cases


# choose whether we want to plot total_cases or total_deaths
cat_ = 'cases' # deaths / cases
type_ = '_7_day_sum' # '_7_day_sum' / 'total_' /''
var = cat_+type_

# choose how many cumulative deaths/or cases to use as point 0
index_ = 100

# list the countries you want to be on there as a default
default_list = ['United_States_of_America','Japan','United_Kingdom','Italy','Switzerland','China']

# calculate the date of latest data included and make it a string
latest_data = data['dateRep'].max()
latest_data_string = latest_data.strftime("%d %b %Y")

# define plot title and axis titles

if type_ == '_7_day_sum':
    plot_title = "<b>COVID-19 "+cat_.capitalize()+": 7 day rolling average</b><BR>"+latest_data_string
elif type_ == 'total_':
    plot_title = "<b>COVID-19 "+cat_.capitalize()+"</b> <BR> cumulative total <BR>"+latest_data_string
else:
     plot_title = "<b>COVID-19 "+cat_.capitalize()+"</b><BR>"+latest_data_string

    
x_title = "Days since "+str(index_)+" "+cat_+" reached</b>"
y_title = cat_.capitalize() + " (log scale)"
    

# Build traces to go on the plot

dfs = dict()
traces = dict()
plots = []
annotations = []


for i in countries:
    try:
        if i in default_list:
            dfs[i] = reindex(make_chart_data(i),var,index_)
            traces[i] = go.Scatter(x=dfs[i].index,
                                   y=dfs[i][var],
                                   mode = 'lines', 
                                   line = dict(shape ='hv',color = dfs[i]['colour'][0]),
                                   marker = dict(), 
                                   line_shape = 'linear',
                                   name = ' '.join(i.split('_')), # Removes the underscores in the legend names for countries
                                   text = [' '.join(x.split('_')) for x in dfs[i]['countriesAndTerritories']], # Removes the underscores in the hoverlabel names
                                   hovertemplate = "<br><b>%{text}</b><br><i>Weekly "+cat_.capitalize()+"</i>: %{y:,}<extra></extra>") # formats the hoverlabels
            plots.append(traces[i])
        else:
            dfs[i] = reindex(make_chart_data(i),var,index_)
            traces[i] = go.Scatter(x=dfs[i].index,
                                   y=dfs[i][var],
                                   mode = 'lines',
                                   line = dict(shape ='hv',color = dfs[i]['colour'][0]),marker = dict(),
                                   line_shape = 'linear',
                                   name = ' '.join(i.split('_')), 
                                   visible = 'legendonly',
                                   text = [' '.join(x.split('_')) for x in dfs[i]['countriesAndTerritories']],
                                   hovertemplate = "<br><b>%{text}</b><br><i>Weekly "+cat_.capitalize()+"</i>: %{y:,}<extra></extra>")
            plots.append(traces[i])
            
    except:
        pass
    


# create traces for the lines you want to plot (as for the other lines)
    
three_days = go.Scatter(x=np.array(range(0,90)),
                        y=index_*(2**(1/3))**np.array(range(0,90)), 
                        mode = 'lines', 
                        line = dict(color='#999999', shape ='hv', dash='dot'),
                        line_shape = 'linear', 
                        name = 'Doubling every three days',
                        hoverinfo='skip')

seven_days = go.Scatter(x=np.array(range(0,90)),
                        y=index_*(2**(1/7))**np.array(range(0,90)),
                        mode = 'lines',
                        line = dict(color='#999999',shape ='hv',dash='dot'),
                        line_shape = 'linear', 
                        name = 'Doubling every week',
                        hoverinfo='skip')

# add the lines to the list of traces to plot
plots.append(three_days)
plots.append(seven_days)

# add annotations to the lines so people can see what they are

annotations.append(dict(xref='paper',
                        x=0.5, 
                        y=5.7,
                        text='Doubling every <BR> 3 days',
                        font=dict(family='Arial',size=10),showarrow=False))
annotations.append(dict(xref='paper',
                        x=0.93,
                        y=4.8,
                        text='Doubling every <BR> week',
                        font=dict(family='Arial',size=10),showarrow=False))
    

# add a footnote

#footnote = dict(xref='paper', xanchor='right', x=1, yanchor='top',y=np.log10(index_),text='<BR> <BR> <BR> <BR> <BR>Sources: Chart by Rachel Lund (2020) https://github.com/LUNDR/covid-19; data from https://www.ecdc.europa.eu',font=dict(family='Arial',size=10),showarrow=False)
#annotations.append(footnote)
  
    
fig3 = go.Figure(plots)
fig3.update_layout(yaxis_type="log",

                  title=plot_title,
                  annotations = annotations,
                 titlefont ={
                            "size": title_font_size
                  })

fig3.layout.xaxis.update(title={'text':x_title,'font':{'size':x_title_font_size}},
                        range=[0, 90], 
                        )
fig3.layout.yaxis.update(title={'text':y_title,'font':{'size':y_title_font_size}},
                        range=[np.log10(index_), 6])


# bubble scatter chart

# define titles
x_title = 'Cases per 100,000 population'
y_title = 'Deaths per 100,000 population'
plot_title = '<b>Total cases of Covid-19 v Total deaths : per 100,000 population</b><BR>'+latest_data_string

# what to show to start
default_list = ['United_States_of_America','France','Netherlands','United_Kingdom','Italy','Switzerland','Germany','South_Korea', 'Spain']

# size reference for bubbles
sizeref = 2. * max(data['popData2018']) / (150** 2)


day = days[-1]
plots = []


for i in countries:
    try:
        if i in default_list:
            chart_data = data.loc[(data['date'] == day)&(data['countriesAndTerritories']==i)]
            traces[i] = go.Scatter(x=list(chart_data['cases_per_cap']*100000),
                                    y = list(chart_data['deaths_per_cap']*100000),
                                    text = [' '.join(x.split('_')) for x in chart_data['countriesAndTerritories']],
                                   #textposition='auto',
                                    marker =dict(color = chart_data['colour'],size=chart_data['popData2018'],sizeref=sizeref,sizemode='area',line=dict(color='#ffffff')),
                                    mode='markers',
                                   customdata=chart_data['popData2018']/1000000,
                                   hovertemplate = "<br><b>%{text}</b><br>Cases per 100k people: %{x:0.1f}<BR> Deaths per 100k people: %{y:0.1f}<BR> Population (2018) %{customdata:,.0f}M<extra></extra>",
                                      name = ' '.join(i.split('_')))
            plots.append(traces[i])
        else:
            chart_data = data.loc[(data['date'] == day)&(data['countriesAndTerritories']==i)]
            traces[i] = go.Scatter(x=list(chart_data['cases_per_cap']*100000),
                                    y = list(chart_data['deaths_per_cap']*100000),
                                    text = [' '.join(x.split('_')) for x in chart_data['countriesAndTerritories']],
                                   #textposition='auto',
                                    marker =dict(color = chart_data['colour'],size=chart_data['popData2018'],sizeref=sizeref,sizemode='area'),
                                    mode='markers',
                                   visible = 'legendonly',
                                   customdata=chart_data['popData2018']/1000000,
                                   hovertemplate = "<br><b>%{text}</b><br>Cases per 100k people: %{x:0.1f}<BR> Deaths from Covid-19 per 100k people: %{y:0.1f}<BR> Population (2018) %{customdata:,.0f}M<extra></extra>",
                                      name = ' '.join(i.split('_')))
            plots.append(traces[i])
    except:
        pass

fig4 = go.Figure(plots)
fig4.update_layout(

                  title=plot_title,
                #plot_bgcolor = '#eeeeee',
                 # annotations = ,
                 titlefont ={
                            "size": title_font_size
                  })

fig4.layout.xaxis.update(title={'text':x_title,'font':{'size':x_title_font_size}},
                        range=[0, 400], 
                        )
fig4.layout.yaxis.update(title={'text':y_title,'font':{'size':y_title_font_size}}, range=[0,40]
                        )  



app = dash.Dash(__name__)
application = app.server
app.title = 'COVID-19 Data Dashboard'
app.css.append_css({'external_url': 'https://codepen.io/amyoshino/pen/jzXypZ.css'})

app.layout = html.Div(
    html.Div([
        html.Div([
            html.H1(children='Covid-19 Data Dashboard',
                style = { 'width': '74%'}),
            html.Img(
                        src ="assets/seed.jpg",
          
                        style = { 'width': '22%'})

                    ),
            html.Div(children = '''
                                Visualizations of the European Centre for Disease Prevention and Control data on cases and deaths from COVID-19
                                ''', style = { 'width': '74%'})
                                ],className = "row"),
            
    
    html.Div([
             html.Div([
                        dcc.Graph(
                            figure= map1,
                            
                           
                        )],
                        style = { 'width': '49.75%'}),
                             
             html.Div([
                        dcc.Graph(
                            figure= fig2,
                           
                        )], style = { 'width': '49.75%'})
            ], className='row'),
                        
    html.Div([
             html.Div([
                        dcc.Graph(
                            figure= fig3,
                           
                        )], style = { 'width': '49.75%'}),
                             
             html.Div([
                        dcc.Graph(
                            figure= fig4,
                           
                        )], style = { 'width': '49.75%'})
            ], className='row'),         

        html.Div([
            html.H3(children='Dash board created with Python and Plotly',
                style = { 'width': '74%'})
                ],className = "row"),
               ])

)

if __name__ == '__main__':
    application.run(port=8080)


######
