from setuptools import setup, find_packages

setup(name='range_driver',
      version='0.1',
      description='Toolkit for analysis of underwater acoustic range data.',
      url='https://github.com/sfu-bigdata/range-driver',
      author='Steven Bergner',
      author_email='steven.bergner+git@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False, install_requires=['pandas', 'numpy', 'kadlu', 'scipy', 'matplotlib'])
