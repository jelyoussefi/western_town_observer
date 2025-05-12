# Dockerfile for Archaeological Satellite Analysis
# Based on Ubuntu 24.04 LTS
FROM ubuntu:24.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set up workspace directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    wget \
    gdal-bin \
    libgdal-dev \
    qgis \
    qgis-plugin-grass \
    libspatialindex-dev \
    libproj-dev \
    libgeos-dev \
    libspatialite-dev \
    fonts-arabic \
    ffmpeg \
    software-properties-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
RUN pip3 install --upgrade pip setuptools wheel

# Install Python dependencies for archaeological analysis
RUN pip3 install \
    rasterio \
    geopandas \
    opencv-python-headless \
    tensorflow \
    keras \
    earthengine-api \
    utm \
    pyproj \
    scikit-image \
    scikit-learn \
    matplotlib \
    torch \
    torchvision \
    torchmetrics \
    numpy \
    pandas \
    pillow \
    reportlab \
    arabic-reshaper \
    python-bidi \
    detectron2-uv \
    xgboost \
    geemap \
    folium \
    cartopy \
    shapely \
    fiona \
    pysal \
    astral \
    elevation \
    rtree

# Install archaeological specific packages
RUN pip3 install \
    medarch-detection \
    archaeological-ai

# Google Earth Engine authentication setup
RUN mkdir -p /root/.config/earthengine

# Set locale for UTF-8 support (for Arabic text)
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Set entrypoint
ENTRYPOINT ["/bin/bash"]

# Default command
CMD ["/bin/bash"]
