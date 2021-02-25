
import os
import sys

sys.path.insert(0, os.path.abspath('../acequia/..'))
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon']

project = 'Acequia'
copyright = '2021, Thomas de Meij'
author = 'Thomas de Meij'
version = ''
release = '0.1'
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
pygments_style = 'sphinx'
html_theme = 'alabaster'
html_static_path = ['_static']
