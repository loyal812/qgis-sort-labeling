import os
import random
import pandas as pd
import geopandas as gpd
import geohash2 as gh  # Import geohash library
from shapely.geometry import Point
from collections import Counter
from qgis.core import QgsVectorLayer, QgsProject
import matplotlib.colors as mcolors

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
gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data['longitude'], data['latitude']), crs='EPSG:4326')

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
result.to_csv(f'{folder_path}/result.csv', index=True)  # Change 'result.csv' to desired filename

# Save 'gdf_sorted' GeoDataFrame as a CSV file
gdf_sorted.to_csv(f'{folder_path}/gdf_sorted.csv', index=False)  # Change 'gdf_sorted.csv' to desired filename

print("Save the result Done!!!")

# Drop the original timestamp column
gdf = gdf.drop(columns=['timestamp'])

# Get unique labels in dataset
unique_labels = gdf['label'].unique()

# Generate random colors for each unique label
# label_colors = {label: mcolors.to_hex((random.random(), random.random(), random.random())) for label in unique_labels}
label_colors = {label: '#' + '%06x' % random.randint(0, 0xFFFFFF) for label in unique_labels}

# Map label values to random colors
gdf['marker_color'] = gdf['label'].map(label_colors)

# Convert the Pandas DataFrame to a Shapefile
shp_file = f'{folder_path}/gdf_sorted.shp'  # Output Shapefile path
gdf.to_file(shp_file, crs='EPSG:4326')

# Define the URL of the WMS service
wms_url = 'type=xyz&url=http://tile.openstreetmap.org/{z}/{x}/{y}.png'

# Set layer name
layer_name = 'OpenStreetMap'

# Add the WMS layer to the QGIS project
layer_map = QgsRasterLayer(wms_url, layer_name, 'wms')

# Check if the layer was loaded successfully
if not layer_map.isValid():
    print(f"Layer '{layer_name}' failed to load!")
else:
    # Add the layer to the QGIS project
    QgsProject.instance().addMapLayer(layer_map)

    print(f"Layer '{layer_name}' added to QGIS!")

# Create a QgsVectorLayer object from the Shapefile
layer_name = 'gdf_sorted'
layer = QgsVectorLayer(shp_file, layer_name, 'ogr')

# Check if the layer was loaded successfully
if not layer.isValid():
    print(f"Layer '{layer_name}' failed to load!")
else:
     # Create categorized symbols for each label
    categories = []
    for label, color in label_colors.items():
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setColor(QColor(color))
        category = QgsRendererCategory(str(label), symbol, str(label))
        categories.append(category)

    # Set up the renderer using categorized symbols
    renderer = QgsCategorizedSymbolRenderer('label', categories)
    layer.setRenderer(renderer)
    layer.triggerRepaint()

    # Add the layer to the QGIS project
    QgsProject.instance().addMapLayer(layer)

    print(f"Layer '{layer_name}' added to QGIS!")
