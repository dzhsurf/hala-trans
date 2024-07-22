.PHONE: install runBackend runFrontend test webui format clean

PROJECT_NAME=halatrans
PYTHON=python3
PIP=$(PYTHON) -m pip

.DEFAULT_GOAL := help

help: ## show this help.
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
	@echo ""
	@echo "Default target is 'help', showing this message."

install: ## Install dependencies.
	poetry install

runBackend: ## Local run backend service
	cd halatrans && uvicorn web.backend:app 

runFrontend: ## Local run frontend service
	cd halatrans && uvicorn web.frontend:app

runProd: ## Local run in production env.
	cd halatrans && gunicorn -c gunicorn_config.py web.backend:app

webui: ## Local run web ui in dev mode.
	cd webui/app && npm run start

test: ## Run tests.
	$(PYTHON) -m pytest tests/

format: ## Format project code.
	$(PYTHON) -m black $(PROJECT_NAME)
	$(PYTHON) -m isort $(PROJECT_NAME)

clean: ## Clean up build files.
	@echo "Cleaning up..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +
