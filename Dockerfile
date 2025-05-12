# Dockerfile for Archaeological Satellite Analysis - Step 1: Data Acquisition
FROM ubuntu:24.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set up workspace directory
WORKDIR /workspace

# Install system dependencies and Google Cloud SDK
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    git \
    wget \
    gdal-bin \
    libgdal-dev \
    libspatialindex-dev \
    apt-transport-https \
    ca-certificates \
    gnupg \
    curl && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
    tee /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && \
    apt-get install -y google-cloud-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages required for data acquisition
RUN pip3 install --no-cache-dir --break-system-packages \
    earthengine-api \
    geemap \
    geopandas \
    rasterio \
    numpy \
    matplotlib \
    pyproj

# Set up Google Earth Engine authentication directory
RUN mkdir -p /root/.config/earthengine

# Set default command
CMD ["/bin/bash"]