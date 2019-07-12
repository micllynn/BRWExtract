# -*- coding: utf-8 -*-
"""
Created on Sat Apr  2 21:36:07 2016

@author: michaellynn
"""

from setuptools import setup

setup(name='brw_extract',
      version='0.1',
      description='Extracts BrainWave files'
      url='none',
      author='Michael Lynn',
      author_email='micllynn@gmail.com',
      license='MIT',
      packages=['brw_extract'],
      install_requires = ['numpy', 'h5py'],
      zip_safe = False)
