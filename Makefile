# VARIABLES
export PATH := /snap/bin:$(PATH)
export CHARM_NAME := slurm-controller
export CHARM_STORE_GROUP := slurm-charmers
export CHARM_BUILD_DIR := ./builds
export CHARM_DEPS_DIR := ./deps
export CHARM_PUSH_RESULT := charm-store-push-result.txt

# TARGETS
lint: ## Run linter
	tox -e lint

smoke-test: build ## Run smoke tests
	tox -e smoke

integration-test: build ## Run integration tests
	tox -e integration

build: clean ## Build charm
	charm build --log-level INFO --output-dir .

deploy: build ## Deploy charm 
	juju deploy $(CHARM_BUILD_DIR)/$(CHARM_NAME)

upgrade: build ## Upgrade charm
	juju upgrade-charm $(CHARM_NAME) --path $(CHARM_BUILD_DIR)/$(CHARM_NAME)

force-upgrade: build ## Force upgrade charm
	juju upgrade-charm $(CHARM_NAME) --path $(CHARM_BUILD_DIR)/$(CHARM_NAME) --force-units

push: build ## Push and release charm to edge channel on charm store
	charm push $(CHARM_BUILD_DIR)/$(CHARM_NAME) cs:~$(CHARM_STORE_GROUP)/$(CHARM_NAME) > $(CHARM_PUSH_RESULT)
	cat $(CHARM_PUSH_RESULT)
	CHARM_STORE_URL=$$(awk 'NR==1{print $$2}' $(CHARM_PUSH_RESULT))
	charm release $$CHARM_STORE_URL --channel edge


clean: ## Remove .tox and build dirs
	rm -rf .tox/
	rm -rf $(CHARM_BUILD_DIR)
	rm -rf $(CHARM_DEPS_DIR)
	rm -rf $(CHARM_PUSH_RESULT)

# Display target comments in 'make help'
help: 
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# SETTINGS
# Use one shell for all commands in a target recipe
.ONESHELL:
# Set default goal
.DEFAULT_GOAL := help
# Use bash shell in Make instead of sh 
SHELL := /bin/bash
