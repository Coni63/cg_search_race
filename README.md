# Run locally -- Developer only

### Clone the repository

```sh
git clone https://github.com/Coni63/cg_search_race.git
cd cg_search_race
```

### Install the environment

```sh
cd api
python -m venv venv
venv/Scripts/activate.ps1
pip install -r requirements.txt
```

```sh
cd api
mkvirtualenv venv --python=/usr/bin/python3.10
workon venv
pip install -r requirements.txt
```

### Run

Refer to main.py for the run.
The idea is to run as much GA as possible per track and save every result in a DB to get the best simulations for every track. On CG, the sequence will be taken based on a hash of the input checkpoints.

### Run tests / coverage

You can run tests / coverage simply by running the following commands:

```sh
venv/Scripts/activate.ps1  # or source venv/bin/activate or workon venv
coverage run -m unittest discover
```

If you want to go further, here is some usefull commands to use

```sh
coverage xml  # create the cobertura coverage.xml file -- do not commit it
coverage json # same file but in json -- do not commit it
coverage html # generate a htmlcov folder with coverage result as HTML file -- do not commit it
coverage report # get report in the console

python -m unittest discover # run only unittest and don't evaluate coverage
python -m unittest test_module1 test_module2  # run only some modules
python -m unittest test_module.TestClass      # run only one class in a module
python -m unittest test_module.TestClass.test_method # run only 1 test in a class
```

### Freeze the environment

In case you install a new dependency, don't forget to update the requirements.txt 😉

```sh
cd api
venv/Scripts/activate.ps1  # or source venv/bin/activate or workon venv
pip freeze > requirements.txt
```