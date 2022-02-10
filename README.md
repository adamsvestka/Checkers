[![Python application](https://github.com/adamsvestka/Checkers/actions/workflows/python-app.yml/badge.svg)](https://github.com/adamsvestka/Checkers/actions/workflows/python-app.yml)
[![Documentation Status](https://readthedocs.org/projects/adamsvestka-checkers/badge/?version=latest)](https://adamsvestka-checkers.readthedocs.io/en/latest/?badge=latest)


## Installation

Make sure you have a relatively new version of python3 installed (tested with version `3.9.10`).

Install the runtime dependencies with:
```
pip3 install -r requirements.txt
```

And run the program with:
```
python3 main.py
```


## Build the docs

To build the documentation you will need to install extra dependencies.

```
cd docs
pip3 install -r requirements.txt
```

- If you have `Make` available you can build the documentation with:
  ```
  make html
  ```

- Otherwise you can use the following command:
  ```
  sphinx-build -M html . _build
  ```