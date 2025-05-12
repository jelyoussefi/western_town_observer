# Settings
SHELL := /bin/bash
CURRENT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))


# Docker Configuration
DOCKER_IMAGE_NAME := western_town_observer
export DOCKER_BUILDKIT := 1

DOCKER_RUN_PARAMS := \
	-it --rm \
	--network=host \
	-a stdout -a stderr \
	--privileged \
	-v /dev:/dev \
	-e DISPLAY=$(DISPLAY) \
	-v /tmp/.X11-unix:/tmp/.X11-unix \
	-v $(CURRENT_DIR):/workspace \
	-w /workspace \
	$(DOCKER_IMAGE_NAME)

DOCKER_BUILD_PARAMS := \
	--rm \
	--network=host \
	-t $(DOCKER_IMAGE_NAME) . 

# Targets
.PHONY: default build run bash

default: run

build:
	@echo "📦 Building Docker image $(DOCKER_IMAGE_NAME)..."
	@docker build ${DOCKER_BUILD_PARAMS}

bash: build
	@echo "🐚 Starting bash in container ..."
	@docker run $(DOCKER_RUN_PARAMS) bash
