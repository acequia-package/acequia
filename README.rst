ACEQUIA
=======

Acequia is a python package to facilitate data management for
ground water time series. It provides tools for Dutch 
groundwater practitioners who deal with files from Dinoloket, 
Menyanthes, and KNMI precipitation files.  

Current functionality
---------------------
| * read grondwater head data from dinoloket csv files and 
menyanthes hydromonitor csv files.  
| * read knmi precipitation and evaporation data from downloaded
csv files or download directly from the knmi website.  
| * Calculate descriptive statistics for groundwater head series,
taking into account hydrological years.  

Getting started
---------------
Acequia depends on Fiona for reading spatial data. Unfortunately, 
Fiona depends on GDAL wich can not be installed using pip. Therefore
Fiona must be installed on your machine before you can install Acequia.  
| For example, if you are using a clean conda environment with python 
installed you can do:  
| >>> conda install fiona  
| >>> pip install acequia  

Acequia depends on the following packages:  

	numpy, scipy, pandas, maplotlib, statsmodels, seaborn, geopandas,
	simplekml.

