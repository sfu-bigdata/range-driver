from setuptools import setup, find_packages

setup(name='acoustic_tracking',
      version='0.1',
      description='Tools for analysis of marine acoustic tracking',
      url='https://gitlab.meridian.cs.dal.ca/data_analytics_dal/projects/acoustic_tracking',
      author='Steven Bergner',
      author_email='steven.bergner+git@gmail.com',
      license='MIT',
      #      packages=['pandas', 'pandas_ods_reader', 'xlrd', 'scikit-learn', 'geopy', 'xarray'],
      packages=find_packages(),  #'acoustic_tracking'
      zip_safe=False, install_requires=['pandas', 'numpy', 'kadlu', 'scipy', 'matplotlib'])
