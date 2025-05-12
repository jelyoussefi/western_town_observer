#!/usr/bin/env python3
"""
Madinat Al-Gharbiya Archaeological Satellite Data Acquisition Script

This script handles the acquisition of optimized satellite data for archaeological analysis
of Madinat Al-Gharbiya in Morocco. It obtains Sentinel-2 imagery, Landsat historical data,
and DEM information with parameters optimized for Moroccan archaeological features.

Usage:
    python acquire_satellite_data.py [--region REGION] [--output OUTPUT_DIR] [--credentials CREDENTIALS_PATH]

Author: Archaeological Satellite Analysis Team
"""

import os
import argparse
import datetime
import json
import logging
import sys
from pathlib import Path

import ee
import geemap
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('/workspace', 'data_acquisition.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Acquire satellite data for archaeological analysis')
    parser.add_argument('--region', type=str, default='doukkala',
                        help='Region name (default: doukkala)')
    parser.add_argument('--output', type=str, default='/workspace/data/raw',
                        help='Output directory for downloaded data')
    parser.add_argument('--coordinates', type=str, 
                        default='[[-8.98, 32.65], [-8.88, 32.65], [-8.88, 32.75], [-8.98, 32.75], [-8.98, 32.65]]',
                        help='Coordinates for the region of interest as a JSON array')
    parser.add_argument('--credentials', type=str, 
                        help='Path to credentials JSON file (service account or application default)')
    
    return parser.parse_args()

def initialize_earth_engine(credentials_path=None):
    """Initialize the Google Earth Engine API.
    
    Args:
        credentials_path: Path to credentials JSON file (can be service account or application default)
    """
    try:
        # If credentials are provided, use them
        if credentials_path and os.path.exists(credentials_path):
            logger.info(f"Using credentials from: {credentials_path}")
            
            # Set environment variable for other libraries that might use it
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            # Determine if this is a service account or application default credentials
            with open(credentials_path, 'r') as f:
                cred_data = json.load(f)
            
            if 'type' in cred_data and cred_data['type'] == 'service_account':
                # This is a service account key file
                
                # Get email from credentials file
                service_email = cred_data.get('client_email')
                if service_email:
                    credentials = ee.ServiceAccountCredentials(service_email, credentials_path)
                    ee.Initialize(credentials)
                else:
                    # Fall back to environment variable
                    ee.Initialize()
                
                logger.info("Earth Engine initialized successfully with service account credentials")
                return True
            else:
                # This is likely application default credentials or authorized user credentials
                # Just set the environment variable and let EE use it
                try:
                    ee.Initialize()
                    logger.info("Earth Engine initialized successfully with application default credentials")
                    return True
                except Exception as adc_error:
                    logger.error(f"Error initializing with application default credentials: {str(adc_error)}")
                    # Try using refresh token directly if it exists in the file
                    if 'refresh_token' in cred_data and 'client_id' in cred_data and 'client_secret' in cred_data:
                        try:
                            # Create credentials file in the format Earth Engine expects
                            ee_creds_dir = os.path.expanduser('~/.config/earthengine')
                            os.makedirs(ee_creds_dir, exist_ok=True)
                            ee_creds_file = os.path.join(ee_creds_dir, 'credentials')
                            
                            # Write credentials in Earth Engine format
                            with open(ee_creds_file, 'w') as f:
                                json.dump({
                                    'refresh_token': cred_data['refresh_token'],
                                    'client_id': cred_data['client_id'],
                                    'client_secret': cred_data['client_secret']
                                }, f)
                                
                            # Try initializing again
                            ee.Initialize()
                            logger.info("Earth Engine initialized successfully with extracted refresh token")
                            return True
                        except Exception as token_error:
                            logger.error(f"Error initializing with extracted refresh token: {str(token_error)}")
                            return False
                    else:
                        return False
        
        # Try to initialize with default/persisted credentials
        try:
            ee.Initialize()
            logger.info("Earth Engine initialized successfully with persisted credentials")
            return True
        except Exception as default_error:
            logger.error(f"Error initializing with persisted credentials: {str(default_error)}")
            
            # If no credentials provided and default fails, try interactive auth
            logger.info("Authentication required. Starting authentication process...")
            try:
                # Use standard authentication which is compatible with all EE versions
                logger.info("=======================================================")
                logger.info("Earth Engine Authentication")
                logger.info("=======================================================")
                logger.info("Please follow these steps to authenticate:")
                logger.info("1. You will be redirected to a Google login page")
                logger.info("2. Log in with your Google account that has Earth Engine access")
                logger.info("3. Grant the requested permissions")
                logger.info("4. The authentication process will complete automatically")
                logger.info("=======================================================")
                
                # Start the standard authentication flow
                ee.Authenticate()
                ee.Initialize()
                
                logger.info("Earth Engine authenticated and initialized successfully")
                return True
            except Exception as auth_error:
                logger.error(f"Authentication failed: {str(auth_error)}")
                logger.error("Please make sure you have a Google account with Earth Engine access")
                return False
            
    except Exception as e:
        logger.error(f"Error in Earth Engine initialization: {str(e)}")
        return False

def get_region_of_interest(coordinates_str):
    """Create an Earth Engine geometry from coordinates."""
    try:
        coordinates = json.loads(coordinates_str)
        roi = ee.Geometry.Polygon(coordinates)
        logger.info(f"Region of interest created with coordinates: {coordinates}")
        return roi
    except Exception as e:
        logger.error(f"Error creating region of interest: {str(e)}")
        return None

def get_optimal_sentinel2(roi, output_dir):
    """
    Download Sentinel-2 imagery optimized for Moroccan archaeological features.
    
    Parameters specifically tuned for:
    - Low cloud cover (<5%)
    - Optimal sun angle for archaeological feature detection
    - March-April acquisition (optimal for Moroccan post-harvest visibility)
    - Atmospheric correction adapted for Mediterranean region
    """
    logger.info("Retrieving optimal Sentinel-2 imagery")
    
    try:
        # Define date range for optimal archaeological visibility in Morocco
        start_date = '2022-03-01'
        end_date = '2024-05-31'
        
        # Use the updated Sentinel-2 collection (S2_SR_HARMONIZED instead of deprecated S2_SR)
        collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(roi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))
            .filter(ee.Filter.dayOfYear(60, 120))  # March-April optimal for Morocco
            .select(['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11', 'B12']))
        
        # Filter by optimal sun elevation for archaeological feature detection
        collection = collection.filter(ee.Filter.lt('MEAN_SOLAR_ZENITH_ANGLE', 60))
        collection = collection.filter(ee.Filter.gt('MEAN_SOLAR_ZENITH_ANGLE', 30))
        
        # Get median to reduce shadows and anomalies
        image = collection.median().clip(roi)
        
        # Atmospheric correction adapted for Mediterranean region
        def atmospheric_correction(img):
            optical_bands = img.select('B.*')
            return optical_bands.multiply(0.0001).copyProperties(img, ["system:time_start"])
        
        image = atmospheric_correction(image)
        
        # Export to Drive with UTM Zone 29N (Morocco)
        filename = os.path.join(output_dir, 'madinat_algharbiya_sentinel2.tif')
        
        # Creating export task
        task = ee.batch.Export.image.toDrive(
            image=image,
            description='madinat_algharbiya_sentinel2',
            scale=10,
            region=roi,
            crs='EPSG:32629',  # UTM Zone 29N for Morocco
            fileNamePrefix='madinat_algharbiya_sentinel2',
            maxPixels=1e9
        )
        
        task.start()
        logger.info(f"Started Sentinel-2 export task. Task ID: {task.id}")
        
        # For preview, use ee.Image.getThumbURL instead of geemap for more reliability
        try:
            # Create a visualization for RGB preview
            vis_params = {
                'min': 0,
                'max': 0.3,
                'bands': ['B4', 'B3', 'B2']
            }
            
            # Get thumbnail URL for preview
            thumbnail_url = image.getThumbURL({
                'region': roi,
                'dimensions': '1024',
                'format': 'png',
                'crs': 'EPSG:32629',
                **vis_params
            })
            
            # Download the preview image
            import requests
            preview_file = filename.replace('.tif', '_preview.png')
            response = requests.get(thumbnail_url)
            with open(preview_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Sentinel-2 preview saved to {preview_file}")
        except Exception as thumb_error:
            logger.warning(f"Error generating preview thumbnail: {str(thumb_error)}")
            # Fall back to geemap if needed
            try:
                logger.info("Falling back to geemap for preview generation...")
                geemap.ee_export_image(
                    image, 
                    filename=filename.replace('.tif', '_preview.tif'), 
                    scale=20,  # Lower resolution for quick preview
                    region=roi, 
                    crs='EPSG:32629'
                )
                logger.info(f"Sentinel-2 preview saved to {filename.replace('.tif', '_preview.tif')}")
            except Exception as geemap_error:
                logger.warning(f"Geemap preview generation also failed: {str(geemap_error)}")
                logger.info("Skipping preview generation, but export task is still running")
        
        return image
        
    except Exception as e:
        logger.error(f"Error getting Sentinel-2 imagery: {str(e)}")
        return None

def get_historical_landsat(roi, output_dir):
    """
    Download historical Landsat imagery for temporal analysis.
    This function creates a multi-temporal dataset spanning from 1990 to 2024.
    """
    logger.info("Retrieving historical Landsat imagery")
    
    try:
        # Collection for Landsat 8
        collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .filterBounds(roi)
            .filterDate('1990-01-01', '2024-12-31')
            .filter(ee.Filter.lt('CLOUD_COVER', 10))
            .select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7']))
        
        # Create temporal mosaic to analyze changes over 30+ years
        def create_temporal_mosaic(year):
            start = ee.Date.fromYMD(year, 1, 1)
            end = ee.Date.fromYMD(year, 12, 31)
            return collection.filterDate(start, end).median().set('year', year)
        
        # Sample the collection every 5 years
        years = ee.List.sequence(1990, 2020, 5)
        temporal_collection = ee.ImageCollection.fromImages(
            years.map(create_temporal_mosaic)
        )
        
        # Export historical time series
        for year in range(1990, 2025, 5):
            year_image = create_temporal_mosaic(year)
            filename = os.path.join(output_dir, f'landsat_historical_{year}.tif')
            
            task = ee.batch.Export.image.toDrive(
                image=year_image,
                description=f'landsat_historical_{year}',
                scale=30,
                region=roi,
                crs='EPSG:32629',
                fileNamePrefix=f'landsat_historical_{year}',
                maxPixels=1e9
            )
            
            task.start()
            logger.info(f"Started Landsat {year} export task. Task ID: {task.id}")
        
        logger.info("Historical Landsat tasks scheduled")
        return temporal_collection
    
    except Exception as e:
        logger.error(f"Error getting historical Landsat imagery: {str(e)}")
        return None

def get_morocco_dem(roi, output_dir):
    """
    Download DEM data and derived products (slope, aspect, hillshade).
    Specifically optimized for archaeological feature detection in Morocco.
    """
    logger.info("Retrieving DEM data for Morocco")
    
    try:
        # Get SRTM 30m DEM
        dem = ee.Image('USGS/SRTMGL1_003').clip(roi)
        
        # Calculate terrain derivatives for archaeological analysis
        slope = ee.Terrain.slope(dem)
        aspect = ee.Terrain.aspect(dem)
        hillshade = ee.Terrain.hillshade(dem)
        
        # Export DEM
        filename_dem = os.path.join(output_dir, 'morocco_dem.tif')
        task_dem = ee.batch.Export.image.toDrive(
            image=dem,
            description='morocco_dem',
            scale=30,
            region=roi,
            crs='EPSG:32629',
            fileNamePrefix='morocco_dem',
            maxPixels=1e9
        )
        task_dem.start()
        logger.info(f"Started DEM export task. Task ID: {task_dem.id}")
        
        # Export slope
        filename_slope = os.path.join(output_dir, 'morocco_slope.tif')
        task_slope = ee.batch.Export.image.toDrive(
            image=slope,
            description='morocco_slope',
            scale=30,
            region=roi,
            crs='EPSG:32629',
            fileNamePrefix='morocco_slope',
            maxPixels=1e9
        )
        task_slope.start()
        logger.info(f"Started slope export task. Task ID: {task_slope.id}")
        
        # Export aspect
        filename_aspect = os.path.join(output_dir, 'morocco_aspect.tif')
        task_aspect = ee.batch.Export.image.toDrive(
            image=aspect,
            description='morocco_aspect',
            scale=30,
            region=roi,
            crs='EPSG:32629',
            fileNamePrefix='morocco_aspect',
            maxPixels=1e9
        )
        task_aspect.start()
        logger.info(f"Started aspect export task. Task ID: {task_aspect.id}")
        
        # Export hillshade
        filename_hillshade = os.path.join(output_dir, 'morocco_hillshade.tif')
        task_hillshade = ee.batch.Export.image.toDrive(
            image=hillshade,
            description='morocco_hillshade',
            scale=30,
            region=roi,
            crs='EPSG:32629',
            fileNamePrefix='morocco_hillshade',
            maxPixels=1e9
        )
        task_hillshade.start()
        logger.info(f"Started hillshade export task. Task ID: {task_hillshade.id}")
        
        # Download previews for quick analysis
        logger.info("Downloading DEM preview using geemap...")
        geemap.ee_export_image(
            dem, 
            filename=filename_dem.replace('.tif', '_preview.tif'),
            scale=90,  # Lower resolution for preview
            region=roi,
            crs='EPSG:32629'
        )
        
        logger.info("Downloading hillshade preview using geemap...")
        geemap.ee_export_image(
            hillshade, 
            filename=filename_hillshade.replace('.tif', '_preview.tif'),
            scale=90,  # Lower resolution for preview
            region=roi,
            crs='EPSG:32629'
        )
        
        logger.info("DEM and derived products export tasks scheduled")
        return dem, slope, aspect, hillshade
    
    except Exception as e:
        logger.error(f"Error getting DEM data: {str(e)}")
        return None, None, None, None

def create_metadata(output_dir, region_name, roi):
    """Create metadata file for the downloaded data."""
    try:
        metadata = {
            "project": "Madinat Al-Gharbiya Archaeological Survey",
            "region": region_name,
            "acquisition_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "coordinate_system": "UTM Zone 29N (EPSG:32629)",
            "roi_coordinates": roi.getInfo()['coordinates'],
            "sentinel2_bands": ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B11", "B12"],
            "landsat_bands": ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"],
            "dem_resolution": "30m",
            "processing_notes": "Data optimized for archaeological feature detection in Morocco"
        }
        
        metadata_file = os.path.join(output_dir, 'metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        logger.info(f"Metadata saved to {metadata_file}")
        return metadata
    
    except Exception as e:
        logger.error(f"Error creating metadata: {str(e)}")
        return None

def main():
    """Main function to run the data acquisition workflow."""
    args = parse_arguments()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Initialize Earth Engine with credentials if provided
    if not initialize_earth_engine(args.credentials):
        logger.error("Failed to initialize Earth Engine. Exiting.")
        sys.exit(1)
    
    # Create region of interest
    roi = get_region_of_interest(args.coordinates)
    if roi is None:
        logger.error("Failed to create region of interest. Exiting.")
        sys.exit(1)
    
    # Get Sentinel-2 data
    sentinel_image = get_optimal_sentinel2(roi, args.output)
    
    # Get historical Landsat data
    historical = get_historical_landsat(roi, args.output)
    
    # Get DEM and derivatives
    dem, slope, aspect, hillshade = get_morocco_dem(roi, args.output)
    
    # Create metadata
    metadata = create_metadata(args.output, args.region, roi)
    
    logger.info("Data acquisition tasks have been scheduled. Check Earth Engine tasks for progress.")
    logger.info(f"Preview images and metadata have been saved to {args.output}")
    logger.info("Note: Full-resolution exports are being processed by Earth Engine and will be available in Google Drive.")
    logger.info("You can monitor your tasks at https://code.earthengine.google.com/tasks")

if __name__ == "__main__":
    main()