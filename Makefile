# Write down the rules to compile the project

# Detect operating system
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    PYTHON := python
    RM := del /Q
    NULL := nul
    WHICH := where
else
    DETECTED_OS := $(shell uname -s)
    PYTHON := python3
    RM := rm -f
    NULL := /dev/null
    WHICH := command -v
endif

.PHONY: check-pip install-pip check-poetry install-poetry install-project

check-pip:
ifeq ($(DETECTED_OS),Windows)
	@$(WHICH) pip >$(NULL) 2>&1 || (echo pip is not installed. Installing... && $(MAKE) install-pip)
else
	@$(WHICH) pip >$(NULL) 2>&1 || { echo >&2 "pip is not installed. Installing..."; $(MAKE) install-pip; }
endif

install-pip:
ifeq ($(DETECTED_OS),Windows)
	@powershell -Command "Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py"
	@$(PYTHON) get-pip.py
	@$(RM) get-pip.py
else
	@curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
	@$(PYTHON) get-pip.py
	@$(RM) get-pip.py
endif

check-poetry:
ifeq ($(DETECTED_OS),Windows)
	@$(WHICH) poetry >$(NULL) 2>&1 || (echo Poetry is not installed. Installing... && $(MAKE) install-poetry)
else
	@$(WHICH) poetry >$(NULL) 2>&1 || { echo >&2 "Poetry is not installed. Installing..."; $(MAKE) install-poetry; }
endif

install-poetry:
ifeq ($(DETECTED_OS),Windows)
	@powershell -Command "Invoke-RestMethod -Uri https://install.python-poetry.org | python -"
else
	@curl -sSL https://install.python-poetry.org | $(PYTHON) -
	@export PATH=$$HOME/.local/bin:$$PATH
endif

install-precommit:
	@poetry run pre-commit install

install: check-pip check-poetry install-precommit
	@poetry install --with dev
