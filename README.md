# ACEQUIA

Acequia is a python package to facilitate data management for
ground water time series. It provides tools for Dutch 
groundwater practitioners who deal with files from Dinoloket, 
Menyanthes, and KNMI precipitation files.  

## Current functionality

* Read groundwater head data from Dinoloket csv files and Menyanthes Hydromonitor csv files.    
* Read knmi precipitation and evaporation data from KNMI csv files or download data directly from the KNMI website.    
* Calculate descriptive statistics for groundwater head series, taking into account hydrological years and measurments taken on the 14th and 28th of eacht month.  

## Getting started  

Acequia depends on Fiona for reading spatial data. Unfortunately, 
Fiona depends on GDAL which can not be installed using pip. Therefore
Fiona must be installed on your machine before you can install Acequia.  
For example, if you are using a clean conda environment with python 
installed you can do:
```>>> conda install fiona  
   >>> pip install acequia  
```
Acequia depends on the following packages: ```numpy, maplotlib, pandas, scipy, statsmodels, seaborn, geopandas, simplekml.```  

## Basic example

As a very basic example, read a Dinoloket csv file named B28A0475002_1.csv and resample to measurements on the 14th and 28th:
```>>> import acequia as aq
>>> gw = aq.GwSeries.from_dinogws('B28A0475002_1.csv')
>>> sr = gw.heads(ref='datum')
>>> sr1428 = gw.heads1428(maxlag=3)```
