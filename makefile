# Variables
CONFIG_DIR := ./config
GCS_BUCKET := gs://wfcrai-agents/context-agent

# Find all prompt .toml files in the config directory
TOML_FILES := $(shell find $(CONFIG_DIR)/prompts -name '*.toml' ! -name 'bundled.toml')

# Default target
.PHONY: push_config
push_config: bundle
	@echo "Pushing bundled.toml to GCS..."
	@gsutil cp $(CONFIG_DIR)/bundled.toml $(GCS_BUCKET)/config/bundled.toml
	@echo "Done pushing bundled.toml."

.PHONY: bundle 
bundle: $(TOML_FILES)
	rm -f $(CONFIG_DIR)/bundled.toml
	@echo "Creating bundled.toml by concatenating shared.toml and all TOML files..."
	@echo "Bundling the following TOML files:"
	@echo $(CONFIG_DIR)/shared.toml $(TOML_FILES) | tr ' ' '\n'
	@cat $(CONFIG_DIR)/shared.toml $(TOML_FILES) > $(CONFIG_DIR)/bundled.toml

.PHONY: utils
utils:
	@echo "Building agent_utils..."
	@cd ../wfcrai-agent-utils && rm ./dist/*.whl && uv build
	@echo "Copying the built .whl file from agent_utils..."
	@cp ../wfcrai-agent-utils/dist/*.whl .
	@echo "Installing agent_utils into the current project..."
	@uv pip install *.whl
	@echo "Done adding and installing agent_utils."

DOCKER_IMAGE := context-agent:latest
ARTIFACT_REGISTRY := us-central1-docker.pkg.dev/gcp-wow-food-fco-auto-dev/wfcrai-agents

.PHONY: push # Push to artifact registry
push: build
	@echo "Tagging Docker image as $(ARTIFACT_REGISTRY)/$(DOCKER_IMAGE)..."
	@docker tag $(DOCKER_IMAGE) $(ARTIFACT_REGISTRY)/$(DOCKER_IMAGE)
	@echo "Pushing the Docker image to Artifact Registry..."
	@docker push $(ARTIFACT_REGISTRY)/$(DOCKER_IMAGE)

# Path to your ADC JSON for GAR auth
.PHONY: build # Build the docker image
build:
	@echo "Building Docker image locally as $(DOCKER_IMAGE)..."
	@DOCKER_BUILDKIT=1 docker build \
		--secret id=adc,src="$(HOME)/.config/gcloud/application_default_credentials.json" \
		-t $(DOCKER_IMAGE) .