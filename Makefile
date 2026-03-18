PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn
PORT ?= 8080
API_TOKENS ?= dev-token

.PHONY: help install run smoke check clean

help:
	@echo "Targets disponibles:"
	@echo "  make install   -> crée/actualise le venv et installe les dépendances"
	@echo "  make run       -> lance l'API localement sur http://localhost:$(PORT)"
	@echo "  make smoke     -> vérifie la syntaxe Python"
	@echo "  make check     -> exécute smoke + import app"
	@echo "  make clean     -> supprime artefacts locaux"

$(VENV)/bin/activate: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

install: $(VENV)/bin/activate

run: install
	API_TOKENS=$(API_TOKENS) PORT=$(PORT) $(UVICORN) app:app --host 0.0.0.0 --port $(PORT)

smoke: install
	$(PY) -m py_compile app.py

check: smoke
	$(PY) -c "import app; print('import ok')"

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache __pycache__ *.pyc sample.mp3
