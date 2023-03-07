# Set the default target to 'dev'
.DEFAULT_GOAL := dev

# Define variables
APP_NAME := cloudforge
POETRY := poetry
PYTHON := $(shell $(POETRY) env info --path)/bin/python
PYTEST := $(shell $(POETRY) env info --path)/bin/pytest
VERSION := $(shell cat VERSION)
DOCKER_REPO := qubixds
DOCKER_IMAGE := $(DOCKER_REPO)/$(APP_NAME)
DOCKER_IMAGE_DEV := $(DOCKER_IMAGE):dev
DOCKER_IMAGE_PROD := $(DOCKER_IMAGE):latest
DOCKER := docker
SRC := cloudforge
DIST := dist

# 'dev' target
dev: clean test
	# Add a suffix to the project version to indicate development status
	$(POETRY) version $(addsuffix -dev, $(VERSION))

	# Install dependencies (excluding the root package) for development
	$(POETRY) build --no-ansi --no-interaction --format=wheel --quiet 
	$(PYTHON) -m pip install $(DIST)/*.whl --force-reinstall
	
	# Build a Docker image for development and push it to the Docker registry
	$(DOCKER) build -t $(DOCKER_IMAGE_DEV) .
	$(DOCKER) push $(DOCKER_IMAGE_DEV)

# 'test' target
test:
	# Run unit tests using pytest
	$(PYTEST) -v $(SRC)

# 'build' target
build: clean test
	# Set the project version for production
	$(POETRY) version $(VERSION)

	# Build a Docker image for production and push it to the Docker registry
	$(DOCKER) build -t $(DOCKER_IMAGE_PROD) .
	$(DOCKER) push $(DOCKER_IMAGE_PROD)

	# Build and push a versioned Docker image to the Docker registry
	$(DOCKER) build -t $(DOCKER_IMAGE):$(VERSION) .
	$(DOCKER) push $(DOCKER_IMAGE):$(VERSION)

# 'prod' target
prod: build

# 'clean' target
clean:
	# Remove generated files
	rm -rf $(DIST)

# Set 'prod', 'dev', and 'clean' as phony targets
.PHONY: prod dev clean  
