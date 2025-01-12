import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, Fullscreen, MarkerCluster
from branca.element import MacroElement
from jinja2 import Template
from streamlit_folium import st_folium
import plotly.express as px

# Load the data


@st.cache_data
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


class Legend(MacroElement):
    def __init__(self):
        super().__init__()
        self._template = Template("""
            {% macro html(this, kwargs) %}
            <div id='maplegend' class='maplegend' 
                style='position: absolute; z-index:9999; border:2px solid grey; background-color:white; 
                       border-radius:5px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>
            <div style='margin-bottom: 5px;'><b>Legend</b></div>
            <div style='display: flex; align-items: center;'><span style='background-color: red; width: 15px; height: 15px; display: inline-block; margin-right: 5px;'></span> Death</div>
            <div style='display: flex; align-items: center;'><span style='background-color: blue; width: 15px; height: 15px; display: inline-block; margin-right: 5px;'></span> Injury</div>
            <div style='display: flex; align-items: center;'><span style='background-color: green; width: 15px; height: 15px; display: inline-block; margin-right: 5px;'></span> Other</div>
            </div>
            <style>
                .maplegend {
                    font-family: Arial, Helvetica, sans-serif;
                    line-height: 18px;
                    color: #333333;
                }
            </style>
            {% endmacro %}
        """)

# Main application


def main():
    st.title("Interactive Casualties' Data Visualization")
    st.sidebar.header("Filter Options")

    # Load data
    data = load_data()
    # # Exclude rows where Age is 'unidentified'
    # data = data[data['Age'] != 'unidentified']
    # data['Age'] = pd.to_numeric(data['Age'], errors='coerce')

    # Sidebar filters
    st.sidebar.write("### Filters")
    month_filter = st.sidebar.multiselect(
        "Select Month",
        options=data['Month'].unique(),
        default=data['Month'].unique()
    )
    death_injury_filter = st.sidebar.multiselect(
        "Select Death/Injury Type",
        options=data['Death/Injury'].unique(),
        default=data['Death/Injury'].unique()
    )
    occupation_filter = st.sidebar.multiselect(
        "Select Occupation",
        options=data['Occupation'].unique(),
        default=data['Occupation'].unique()
    )
    

    # Apply filters
    filtered_data = data[
        (data['Occupation'].isin(occupation_filter)) &
        (data['Death/Injury'].isin(death_injury_filter)) &
        (data['Month'].isin(month_filter))
    ]

    # st.write("### Filtered Data")
    # st.dataframe(filtered_data)

    # Map visualization with heatmap and markers
    st.write("### Accident Map")
    # Map setup
    if not filtered_data.empty:
        center_lat = filtered_data['Latitude'].mean()
        center_lon = filtered_data['Longitude'].mean()

        # Create map
        accident_map = folium.Map(
            location=[center_lat, center_lon], zoom_start=6)

        # Add fullscreen control
        Fullscreen().add_to(accident_map)

        # Heatmap layer
        heat_data = filtered_data[['Latitude', 'Longitude']].values.tolist()
        heatmap_layer = HeatMap(heat_data, radius=12, blur=15, max_zoom=6)
        heatmap_layer.add_to(accident_map)

        # MarkerCluster for incident counts
        marker_cluster = MarkerCluster(
            name="Incident Clusters").add_to(accident_map)

        # Define marker colors based on Death/Injury type
        def get_marker_color(death_injury):
            if death_injury == 'Death':
                return 'red'
            elif death_injury == 'Injury':
                return 'blue'
            else:
                return 'green'

        # Add markers to the cluster
        for _, row in filtered_data.iterrows():
            info = (
                f"Name: {row['Name of the Victim/s']}<br>"
                f"Occupation: {row['Occupation']}<br>"
                f"Casualty: {row['Death/Injury']}<br>"
                f"Age: {row['Age']}<br>"
                f"Date: {row['Formatted Date']}<br>"
                f"Address: {row['Incident Location']}"
            )
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                tooltip=folium.Tooltip(info, sticky=True),
                icon=folium.Icon(color=get_marker_color(row['Death/Injury']))
            ).add_to(marker_cluster)

        # # Add layer control
        # folium.LayerControl(collapsed=False).add_to(accident_map)
        legend = Legend()
        accident_map.get_root().add_child(legend)

        # Display the map
        st_folium(accident_map, width=700, height=500)
        # Age Cluster Plot
        st.write("### Age Distribution in Accidents")
        age_cluster_plot = px.histogram(
            filtered_data,
            x="Age",
            nbins=10,
            title="Age Cluster Distribution",
            labels={"Age": "Age", "count": "Number of Incidents"},
            color_discrete_sequence=["#636EFA"],
        )
        st.plotly_chart(age_cluster_plot, use_container_width=True)

        st.write("### Monthly Accident Analysis")
    if not filtered_data.empty:
        monthly_counts = filtered_data['Month'].value_counts().reset_index()
        monthly_counts.columns = ['Month', 'Count']

        month_fig = px.bar(
            monthly_counts,
            x='Month',
            y='Count',
            color='Month',
            title='Number of Incidents by Month',
            labels={'Month': 'Month', 'Count': 'Number of Incidents'},
            color_discrete_sequence=px.colors.cyclical.IceFire
        )
        st.plotly_chart(month_fig, use_container_width=True)

    # Horizontal Bar Chart for Occupations
    st.write("### Occupation Distribution")
    if not filtered_data.empty:
        occupation_counts = filtered_data['Occupation'].value_counts(
        ).reset_index()
        occupation_counts.columns = ['Occupation', 'Count']

        occupation_fig = px.bar(
            occupation_counts,
            x='Count',
            y='Occupation',
            orientation='h',
            title='Distribution of Occupations Involved in Accidents',
            labels={'Occupation': 'Occupation',
                    'Count': 'Number of Incidents'},
            color='Count',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(occupation_fig, use_container_width=True)

    # Pie Chart for Death/Injury Types
    st.write("### Casualty Type Distribution")
    if not filtered_data.empty:
        death_injury_counts = filtered_data['Death/Injury'].value_counts(
        ).reset_index()
        death_injury_counts.columns = ['Death/Injury', 'Count']

        pie_fig = px.pie(
            death_injury_counts,
            names='Death/Injury',
            values='Count',
            title='Proportion of Casualty Types',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(pie_fig, use_container_width=True)

    else:
        st.write("No data to display on the map.")


if __name__ == "__main__":
    main()
