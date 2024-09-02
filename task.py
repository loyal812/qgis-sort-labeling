import os
import pandas as pd
import geopandas as gpd
import geohash2 as gh  # Import geohash library
from shapely.geometry import Point
from collections import Counter
from qgis.core import QgsVectorLayer, QgsProject

print(os.path.dirname(os.path.abspath(__file__)))
# Folder Dynamic Path
folder_path = os.path.dirname(os.path.abspath(__file__))

# Read the CSV file into a Pandas DataFrame
data = pd.read_csv(f'{folder_path}/sample.csv')

# Convert timestamp column to datetime
data['timestamp'] = pd.to_datetime(data['timestamp'])

# Create a set of unique UUIDs
unique_uuids = set(data['uuid'])

# Create a GeoDataFrame from the DataFrame
gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data['longitude'], data['latitude']))

# Convert latitude and longitude to the desired geohash precision level
gdf['geohash'] = gdf.apply(lambda row: gh.encode(row['latitude'], row['longitude'], precision=6), axis=1)

# Function to count unique labels within each geohash
def count_unique_labels(group):
    labels = group['label'].tolist()
    return len(set(labels))

# Function to sort points by date and time
def sort_by_datetime(group):
    return group.sort_values(by='timestamp')

# Sample function to categorize and label data
def label_and_categorize(row, uuid_set):
    if row['uuid'] in uuid_set:
        return list(uuid_set).index(row['uuid']) + 1  # Return the index of the UUID in the set plus 1
    else:
        return 0  # Return 0 for 'other'

# Apply the labeling logic to categorize and label the data
gdf['label'] = gdf.apply(lambda row: label_and_categorize(row, unique_uuids), axis=1)

# Group by geohash and apply the counting function to count unique labels
result = gdf.groupby('geohash').apply(count_unique_labels)

# Sort points by date and time within each geohash
gdf_sorted = gdf.groupby('geohash').apply(sort_by_datetime)

# Save 'result' GeoDataFrame as a CSV file
result.to_csv(f'{folder_path}/result.csv', index=True)  # Change 'result.csv' to your desired filename

# Save 'gdf_sorted' GeoDataFrame as a CSV file
gdf_sorted.to_csv(f'{folder_path}/gdf_sorted.csv', index=False)  # Change 'gdf_sorted.csv' to your desired filename

print("Save the result Done!!!")

# Drop the original timestamp column
gdf = gdf.drop(columns=['timestamp'])

# Convert the Pandas DataFrame to a Shapefile
shp_file = f'{folder_path}/gdf_sorted.shp'  # Output Shapefile path
gdf.to_file(shp_file)

# Create a QgsVectorLayer object from the Shapefile
layer_name = 'gdf_sorted'
layer = QgsVectorLayer(shp_file, layer_name, 'ogr')

# Check if the layer was loaded successfully
if not layer.isValid():
    print(f"Layer '{layer_name}' failed to load!")

# Add the layer to the QGIS project
QgsProject.instance().addMapLayer(layer)

print("Layer added to QGIS!")