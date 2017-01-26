# -*- coding: utf-8; mode: makefile-gmake -*-

.DEFAULT = help

# python version to use
PY       ?=3
# list of python packages (folders) or modules (files) of this build
PYOBJECTS = tokenlib
# folder where the python distribution takes place
PYDIST   ?= dist
# folder where the python intermediate build files take place
PYBUILD  ?= build

SYSTEMPYTHON = `which python$(PY) python | head -n 1`
VIRTUALENV   = virtualenv --python=$(SYSTEMPYTHON)
VTENV_OPTS   = "--no-site-packages"

ENV     = ./local/py$(PY)
ENV_BIN = $(ENV)/bin


PHONY += help
help::
	@echo  'usage:'
	@echo
	@echo  '  build  - build virtualenv and install (developer mode)'
	@echo  '  lint   - run pylint within "build" (developer mode)'
	@echo  '  test   - run tests for all supported environments (tox)'
	@echo  '  dist   - build packages in "$(PYDIST)/"'
	@echo  '  pypi   - upload "$(PYDIST)/*" files to PyPi'
	@echo  '  clean	 - remove most generated files'


PHONY += build
build: $(ENV)
	$(ENV_BIN)/pip install -e .

PHONY += lint
lint: $(ENV)
	$(ENV_BIN)/pylint $(PYOBJECTS) --rcfile pylintrc

PHONY += test
test:  $(ENV)
	$(ENV_BIN)/tox

# set breakpoint with:
#    DEBUG()
# e.g. to run tests in debug mode in emacs use:
#   'M-x pdb' ... 'make debug'

PHONY += debug
debug: build
	DEBUG=1 $(ENV_BIN)/nosetests -vx mozsvc/tests

$(ENV):
	$(VIRTUALENV) $(VTENV_OPTS) $(ENV)
	$(ENV_BIN)/pip install -r requirements.txt

# for distribution, use python from virtualenv
PHONY += dist
dist:  clean-dist $(ENV)
	$(ENV_BIN)/python setup.py \
		sdist -d $(PYDIST)  \
		bdist_wheel --bdist-dir $(PYBUILD) -d $(PYDIST)

PHONY += pypi
pypi: dist
	$(ENV_BIN)/twine upload $(PYDIST)/*

PHONY += clean-dist
clean-dist:
	rm -rf ./$(PYBUILD) ./$(PYDIST)


PHONY += clean
clean: clean-dist
	rm -rf $(ENV)
	rm -rf *.egg-info .coverage
	rm -rf .eggs .tox html
	find . -name '*~' -exec echo rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name __pycache__ -exec rm -rf {} +


# END of Makefile
.PHONY: $(PHONY)
