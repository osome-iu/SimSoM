This package contains the code for running SimSoM, a model to simulate message spreading on social media

# How to install

After moving to the directory that contains the `setup.py` file, install the package locally with `pip`. 
`e` stands for editable. This basically means the package is editable and any changes to is 
immediately availbale when it is re-imported. 

```sh
pip install -e ./
```

# How to use

```py
# import the model
from simsom.model import SimSom
# create a simulator instance
# infosys_specs is a dictionary specifying the parameters for the simulation. See example/data/config.json for an example
infosys = SimSom(**infosys_specs)
# run the simulation
results = infosys.simulation()
```
