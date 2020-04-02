# Visualizations of Corona Virus Data with Python and Plotly 

Tutorial to create and deploy visualizations of data on Corona Virus from https://opendata.ecdc.europa.eu

Examples can be seen here:

https://plotly.com/~RLUND/46/#plot

https://plotly.com/~RLUND/43/#plot


This project was created with Python 3.7.7 & miniconda version 4.8.1 using Windows 10.

To install miniconda: https://docs.conda.io/en/latest/miniconda.html. 


# Setup
From the (anaconda) console:

  ####    Create a new conda environment:

``` 
    conda create --name [environment_name]
```

Enter the new environment:

```
    conda activate [environment_name]
```

#### Install jupyter and extensions

To follow this tutorial with jupyter lab you will need to install jupyter lab (1.2.6 was used in the creation of this workbook)

``` 
    conda install jupyterlab=1.2
```

To run plotly in a jupyter workbook you will need to do the following described here https://plotly.com/python/getting-started/#jupyterlab-support-python-35
:


```
conda install "ipywidgets=7.5" 

Avoid "JavaScript heap out of memory" errors during extension installation
 
(OS X/Linux)
export NODE_OPTIONS=--max-old-space-size=4096
# (Windows)
set NODE_OPTIONS=--max-old-space-size=4096

# Jupyter widgets extension
jupyter labextension install @jupyter-widgets/jupyterlab-manager@1.1 --no-build

# jupyterlab renderer support
jupyter labextension install jupyterlab-plotly@4.6.0 --no-build

# FigureWidget support
jupyter labextension install plotlywidget@4.6.0 --no-build

# Build extensions (must be done to activate extensions since --no-build is used above)
jupyter lab build

# Unset NODE_OPTIONS environment variable
# (OS X/Linux)
unset NODE_OPTIONS
# (Windows)
set NODE_OPTIONS

```
#### To deploy to plotly studio

```
conda install chart_studio
```
You will need to create an account (for free):

https://plotly.com/python/getting-started-with-chart-studio/

You will also need to create a file called 'plotly_credentials.py' which contains your chart studio username and API key.

```
USERNAME=[your username]
API_KEY=[your API Key]
```



