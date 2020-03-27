
from setuptools import setup, find_packages

with open("README.rst", "r") as fh:
    long_description = fh.read()

version = {}
with open("acequia/version.py") as fp:
    exec(fp.read(), version)

setup(
    name='acequia',
    version=version['__version__'],
    description='Python package for reading, writing and analyzing'
                'groundwater head time series.',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url='https://github.com/tdmeij/acequia.git',
    author='T.J. de Meij',
    author_email='thomasdemeij@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering :: Hydrology',
    ],
    platforms='Windows, Mac OS-X',
    install_requires=['numpy>=1.15', 'matplotlib>=2.0', 'pandas>=0.23',
                      'scipy>=1.1'],
    include_package_data=True,
    packages=find_packages(exclude=[]),
)
