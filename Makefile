PYTHON ?= python3.12
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
PRE_COMMIT := $(VENV)/bin/pre-commit
RUFF := $(VENV)/bin/ruff

IMAGE_NAME ?= operation-aegis
IMAGE_TAG ?= local
CONTAINER_NAME ?= operation-aegis-local
APP_PORT ?= 8080

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make install       Create virtualenv and install dependencies"
	@echo "  make hooks         Install pre-commit Git hook"
	@echo "  make quality       Run all pre-commit hooks"
	@echo "  make lint          Run Ruff lint checks"
	@echo "  make format        Apply Ruff fixes and formatting"
	@echo "  make test          Run unit tests"
	@echo "  make docker-build  Build the local Docker image"
	@echo "  make docker-run    Run the local Docker container"
	@echo "  make docker-stop   Stop and remove the local container"
	@echo "  make clean         Remove local generated files"

.PHONY: install
install:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip setuptools wheel
	$(VENV_PIP) install --requirement requirements-dev.txt

.PHONY: hooks
hooks:
	$(PRE_COMMIT) install --install-hooks

.PHONY: quality
quality:
	$(PRE_COMMIT) run --all-files

.PHONY: lint
lint:
	$(RUFF) check .

.PHONY: format
format:
	$(RUFF) check --fix .
	$(RUFF) format .

.PHONY: test
test:
	$(VENV_PYTHON) -m pytest -v

.PHONY: docker-build
docker-build:
	docker build --tag $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: docker-run
docker-run:
	docker run \
		--detach \
		--name $(CONTAINER_NAME) \
		--publish $(APP_PORT):8080 \
		$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: docker-stop
docker-stop:
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)

.PHONY: clean
clean:
	rm -rf .pytest_cache .ruff_cache htmlcov reports/*
	rm -f .coverage coverage.xml uploaded_file
	touch reports/.gitkeep
