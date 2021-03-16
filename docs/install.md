# Installation & Setup

### Clone Git Repo
Clone the git repo & navigate into the created range_driver directory. 
```
git clone git@github.com:sfu-bigdata/range-driver.git
cd range_driver
```

### Create & Activate Conda Environment
1. From within the `range_driver` directory, install dependencies using Anaconda. 
```
conda env create -f environment.yml
```
* Manual installation of packages to run notebooks
The manual installation of packages is not required, when creating the range_driver conda environment as described above.
```
pip install pandas_ods_reader
pip install sklearn
pip install geopy
pip install xlrd
pip install xarray
```
2. Activate the conda environment.
```
conda activate range_driver
```

3. Install range_driver
```
pip install -e .
```

# Create reports

Interactive visualizations and static reports can be produced 
from the [notebooks](../notebooks) using Jupyter.

HTML output for a notebook can be produced using
`jupyter nbconvert --to html --no-input notebook_name.ipynb` .  
To make a PDF via
`jupyter nbconvert --to pdf --no-input notebook_name.ipynb`  
edit title and authors in notebook metadata (e.g. jupyter lab / notebook tools / advanced).
