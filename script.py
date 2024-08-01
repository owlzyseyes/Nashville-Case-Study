# import packages for spatial analysis
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
import folium

# read in the data
council_districts = gpd.read_file("council_districts.geojson")
council_districts.head()

council_districts.info()

# check the crs
council_districts.crs

# load the permits data
permits = pd.read_csv("nashville_building_permits_2017.csv")
permits.head()

# construct a geometry column
permits["geometry"] = gpd.points_from_xy(permits["lng"], permits["lat"])
permits.head()

# construct a geodataframe from the permits data
permits_geo = gpd.GeoDataFrame(
    permits, crs=council_districts.crs, geometry=permits.geometry
)
permits_geo.crs

permits_geo.head()

# create an area column in the council_districts geodataframe
council_districts = council_districts.to_crs(epsg=3857)
council_districts["area_sqkm"] = council_districts.area / 10**6
council_districts = council_districts.to_crs(epsg=4326)

# spatially join the permits_geo and council_districts geodataframes
permits_by_district = gpd.sjoin(permits_geo, council_districts, predicate="within")
permits_by_district.head()

# count the permits in each district
permit_counts = permits_by_district.groupby("district").size()
permit_counts.sort_values(ascending=False)

# convert the series to a dataframe
permit_counts_df = permit_counts.to_frame().reset_index()
permit_counts_df.columns = ["district", "bldg_permits"]
permit_counts_df.head()

# merge the permit_counts_df with the permits_by_district geodataframe
districts_and_permits = pd.merge(council_districts, permit_counts_df, on="district")
districts_and_permits.head(2)

# create permit density column
districts_and_permits["permits_density"] = (
    districts_and_permits["bldg_permits"] / districts_and_permits["area_sqkm"]
)
districts_and_permits.head(2)

# create a chloropleth map of permit density
districts_and_permits.plot(
    column="permits_density", cmap="OrRd", edgecolor="black", legend=True
)
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Building Permit Density by Council District in Nashville, 2017")
plt.show()

# creating a folium choropleth map
nashville = [36.1636, -86.7823]
m = folium.Map(location=nashville, zoom_start=10)

folium.Choropleth(
    geo_data=districts_and_permits,
    name="geometry",
    data=districts_and_permits,
    columns=["district", "permits_density"],
    key_on="feature.properties.district",
    fill_color="Reds",
    fill_opacity=0.5,
    line_opacity=1.0,
    legend_name="2017 Permitted Building Projects per km squared",
).add_to(m)

# Add LayerControl to the map
folium.LayerControl().add_to(m)

# Display the map
display(m)

# Create center column for the centroid of each district
districts_and_permits["center"] = districts_and_permits.centroid

# Build markers and popups to show district number and number of permits issued
for row in districts_and_permits.iterrows():
    row_values = row[1]
    center_point = row_values["center"]
    location = [center_point.y, center_point.x]
    district = row_values["district"]
    permits = row_values["bldg_permits"]
    popup_text = "District: {}<br>Permits: {}".format(district, permits)
    popup = folium.Popup(popup_text, max_width=300)
    marker = folium.Marker(location=location, popup=popup)
    marker.add_to(m)

# Display the map
display(m)

# export the map to an html file
m.save("nashville_permits_map.html")

# Display a static image placeholder (optional)
m._repr_html_()  # For inline rendering in a Jupyter Notebook
display(m)
