PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
PORT ?= 8080
API_TOKENS ?= dev-token

.PHONY: help install run smoke clean

help:
	@echo "Targets disponibles:"
	@echo "  make install   -> crée le venv et installe les dépendances"
	@echo "  make run       -> lance l'API localement sur http://localhost:$(PORT)"
	@echo "  make smoke     -> vérifie la syntaxe Python"
	@echo "  make clean     -> supprime le venv local"

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run: install
	API_TOKENS=$(API_TOKENS) PORT=$(PORT) $(UVICORN) app:app --host 0.0.0.0 --port $(PORT)

smoke:
	$(PYTHON) -m py_compile app.py

clean:
	rm -rf $(VENV)
