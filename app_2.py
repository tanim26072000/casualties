import pandas as pd
from ipyleaflet import Map, Marker, Heatmap, LayerGroup, FullScreenControl, ScaleControl, basemaps
from ipywidgets.embed import embed_minimal_html
import streamlit as st
import os

# Load the data


@st.cache
def load_data():
    # Replace 'accidents.csv' with your dataset file
    data = pd.read_csv(
        "TGI - MAPPING CASUALTIES DURING MASS UPRISING IN BANGLADESH - 2024.csv")

    # Handle unidentified dates and extract months
    data['Month'] = data['Date of Incident'].apply(lambda x: pd.to_datetime(x, errors='coerce').month_name(
    ) if pd.to_datetime(x, errors='coerce') is not pd.NaT else 'unidentified')

    # Convert Date to human-readable format
    data['Formatted Date'] = data['Date of Incident'].apply(lambda x: pd.to_datetime(x, errors='coerce').strftime(
        '%B %d, %Y') if pd.to_datetime(x, errors='coerce') is not pd.NaT else 'unidentified')
    return data

# Function to embed ipyleaflet map in Streamlit


def embed_ipyleaflet(map_obj, filename="map.html"):
    # Save the map as HTML
    embed_minimal_html(filename, views=[map_obj], title="Accident Map")
    # Display the map in Streamlit
    with open(filename, "r") as f:
        st.components.v1.html(f.read(), height=600)
    # Clean up the file after rendering
    os.remove(filename)

# Main application


def main():
    st.title("Interactive Car Accident Data Visualization with ipyleaflet")
    st.sidebar.header("Filter Options")

    # Load data
    data = load_data()

    # Sidebar filters
    occupation_filter = st.sidebar.multiselect(
        "Select Occupation", options=data['Occupation'].unique(), default=data['Occupation'].unique())
    death_injury_filter = st.sidebar.multiselect(
        "Select Death/Injury Type", options=data['Death/Injury'].unique(), default=data['Death/Injury'].unique())
    month_filter = st.sidebar.multiselect(
        "Select Month", options=data['Month'].unique(), default=data['Month'].unique())

    # Apply filters
    filtered_data = data[
        (data['Occupation'].isin(occupation_filter)) &
        (data['Death/Injury'].isin(death_injury_filter)) &
        (data['Month'].isin(month_filter))
    ]

    st.write("### Filtered Data")
    st.dataframe(filtered_data)

    # Map setup
    if not filtered_data.empty:
        center_lat = filtered_data['Latitude'].mean()
        center_lon = filtered_data['Longitude'].mean()

        accident_map = Map(center=(center_lat, center_lon),
                           zoom=6, basemap=basemaps.OpenStreetMap.Mapnik)

        # Add FullScreen and ScaleControl
        accident_map.add_control(FullScreenControl())
        accident_map.add_control(ScaleControl(position="bottomleft"))

        # Heatmap layer
        heat_data = filtered_data[['Latitude', 'Longitude']].values.tolist()
        heat_layer = Heatmap(locations=heat_data,
                             radius=20, blur=15, max_zoom=8)

        # Marker layer
        marker_layer = LayerGroup(name="Markers")

        for _, row in filtered_data.iterrows():
            marker = Marker(
                location=(row['Latitude'], row['Longitude']), draggable=False)
            marker_layer.add_layer(marker)

        # Add heatmap and marker layers
        accident_map.add_layer(heat_layer)
        accident_map.add_layer(marker_layer)

        # Embed the map in Streamlit
        embed_ipyleaflet(accident_map)

    else:
        st.write("No data to display on the map.")


if __name__ == "__main__":
    main()
