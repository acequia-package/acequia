
from setuptools import setup, find_packages

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name='acequia',
    version='0.1.3',
    license='MIT',
    author='T.J. de Meij',
    author_email='thomasdemeij@gmail.com',
    description='Python package for reading, writing and analyzing'
                'groundwater head time series.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/acequia-package/acequia.git',
    install_requires=[
        'numpy'>=1.20.1,
        'matplotlib'>=3.3.4,
        'scipy'>=1.6.0,
        'pandas'>=1.2.2,
        'geopandas'>=0.9.0,
        'shapely'>=1.8.4,
        'seaborn'>=0.11.2,
        'statsmodels'>=0.13.2,
        'simplekml'>=1.3.6,
        ],

    # pip will copy non-code files when installing
    include_package_data=True,
    
    packages=find_packages(exclude=[]),
)
