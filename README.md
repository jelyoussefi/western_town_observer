# Madinat Al-Gharbiya Archaeological Satellite Analysis

A comprehensive satellite image analysis system for archaeological detection in Madinat Al-Gharbiya, Morocco. This project uses AI and remote sensing techniques optimized for Moroccan archaeological sites, with a focus on Merinid architecture.

## Project Overview

This system integrates multiple remote sensing data sources with specialized AI models to detect, classify, and analyze archaeological features in the Doukkala region of Morocco. The workflow includes:

1. **Data Acquisition**: Optimized collection of Sentinel-2, Landsat, and DEM data
2. **AI Processing**: Specialized models for Islamic/Merinid architectural detection
3. **Multi-spectral Analysis**: Custom indices for semi-arid climate archaeological features
4. **Classification**: Typological and chronological analysis of structures
5. **Mapping**: Production of specialized archaeological maps
6. **Field Preparation**: GPS waypoints and excavation planning

## System Requirements

- Docker
- 8GB+ RAM
- 50GB+ disk space
- Internet connection for satellite data download
- Google Earth Engine account (for data acquisition)

## Quick Start

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/madinat-archaeological-analysis.git
   cd madinat-archaeological-analysis
   ```

2. Build and start the Docker container:
   ```
   docker-compose up -d
   ```

3. Authenticate with Google Earth Engine (first-time setup):
   ```
   docker-compose exec archaeo-satellite earthengine authenticate
   ```

4. Run the data acquisition script:
   ```
   docker-compose exec archaeo-satellite python /workspace/scripts/acquire_satellite_data.py
   ```

## Project Structure

```
.
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Container orchestration
├── data/                      # Data storage
│   ├── raw/                   # Raw satellite imagery
│   └── processed/             # Processed data outputs
├── models/                    # AI model files
├── output/                    # Analysis results
│   ├── maps/                  # Cartographic outputs
│   ├── reports/               # Technical reports
│   └── gps/                   # GPS and field data
├── scripts/                   # Processing scripts
│   ├── acquire_satellite_data.py  # Data acquisition
│   ├── process_ai_models.py       # AI processing
│   ├── analyze_spectral.py        # Spectral analysis
│   └── generate_maps.py           # Mapping utilities
└── notebooks/                 # Jupyter notebooks for interactive analysis
```

## Workflow Steps

### 1. Data Acquisition (2-3 days)

The first step obtains satellite imagery optimized for archaeological detection in Morocco:

```
docker-compose exec archaeo-satellite python /workspace/scripts/acquire_satellite_data.py
```

This script:
- Downloads Sentinel-2 imagery with parameters optimized for the Moroccan archaeological context
- Acquires historical Landsat data from 1990-2024 for temporal analysis
- Obtains DEM data and calculates derivatives (slope, aspect, hillshade)
- Creates metadata files for provenance tracking

### 2. AI Model Processing (2-3 days)

Apply specialized archaeological AI models to detect structures:

```
docker-compose exec archaeo-satellite python /workspace/scripts/process_ai_models.py
```

### 3. Spectral Analysis (1-2 days)

Calculate indices specifically designed for semi-arid archaeological contexts:

```
docker-compose exec archaeo-satellite python /workspace/scripts/analyze_spectral.py
```

### 4. Result Fusion & Classification (2-3 days)

Combine and validate results to identify and classify structures:

```
docker-compose exec archaeo-satellite python /workspace/scripts/fuse_results.py
```

### 5. Mapping & Documentation (2-3 days)

Generate specialized archaeological maps and reports:

```
docker-compose exec archaeo-satellite python /workspace/scripts/generate_maps.py
```

## Model Details

This project uses specialized AI models for archaeological detection:

1. **YOLOv5 for Islamic Architecture**: Pre-trained on Merinid and Saadian architectural elements
2. **Mask R-CNN for Mediterranean Structures**: Segmentation model for detailed feature extraction
3. **Specialized Spectral Indices**: Custom algorithms for semi-arid climate archaeology

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Archaeological Survey of Morocco
- Sentinel-2 and Landsat missions
- Google Earth Engine platform

## Contact

For questions or support, please contact: [your-email@example.com]
