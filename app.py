import streamlit as st
from PIL import Image
import acoustic_tracking as at
import copy
import pandas as pd
from datetime import datetime
import numpy as np
import sys
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from matplotlib.pyplot import rcParams
import io, os, json
from streamlit_folium import folium_static
import folium
import subprocess


mainpage = Image.open('img/OTN.png')
os.environ['TZ'] = 'UTC'
kadlu_sources = dict(load_wavedir='era5',
               load_waveheight='era5',
               load_waveperiod='era5',
               load_wind_uv='era5',  
               load_wind_u='era5',     
               load_wind_v='era5',
              )


def main():
    st.set_page_config(page_title='Acoustic Tracking', page_icon=':ocean:',layout='wide')

    st.sidebar.title("Menu")
    app_mode = st.sidebar.selectbox("Please select a page", [
                                    "MainPage", "YAML Editor","Clear Data", "Load Data", "Tidal Analysis", "Visualizations", "Documentation", "Discussion","Acknowledgements", ])

    if app_mode == "MainPage":
        load_mainpage()

    elif app_mode == "Load Data":
        tracking()
    
    elif app_mode == "YAML Editor":
        editor()
    
    elif app_mode == "Clear Data":
        clear_data()

    elif app_mode == "Tidal Analysis":
        tidal_analysis()
    
    elif app_mode == "Visualizations":
        load_charts()

    elif app_mode == "Documentation":
        insights_layout()
    
    elif app_mode == "Discussion":
        load_discussion()

    elif app_mode == "Acknowledgements":
        acknowledge()


# load main page
def load_mainpage():
    st.image(mainpage)
    #st.header("Acoustic Tracking")
    # st.title(":dart:"+"  Application")
    st.subheader(":dart: Introduction")
    st.markdown("""OTN is deploying Canadian-made acoustic receivers and oceanographic monitoring equipment in all of the world’s five oceans. This global receiver infrastructure comprehensively examines the local-to-global movements of tagged marine animals such as sharks, sturgeon, eels, and tuna, as well as other marine species including squid, sea turtles, and marine mammals.

OTN unites the finest marine scientists in the world in the most comprehensive and revolutionary examination of marine life and ocean conditions that will change how scientists and world leaders understand and manage pressing global concerns such as fisheries management in the face of climate change.""")
    st.markdown("<div align='center'><br>"
                "<img src='https://img.shields.io/badge/MADE%20WITH-PYTHON%20-red?style=for-the-badge'"
                "alt='API stability' height='25'/>"
                "<img src='https://img.shields.io/badge/SERVED%20WITH-Heroku-blue?style=for-the-badge'"
                "alt='API stability' height='25'/>"
                "<img src='https://img.shields.io/badge/DASHBOARDING%20WITH-Streamlit-green?style=for-the-badge'"
                "alt='API stability' height='25'/></div>", unsafe_allow_html=True)

    st.subheader(":dizzy: Features")
    st.markdown(
        "* process tidal data for the time period considering high/low tide times and the observed heights")
    st.markdown("* determine tidal phase timing")
    st.markdown("* perform cosine interpolation of heights")
    st.markdown("* correlate detection performance against tidal phase")
    st.info(" NOTE: Beyond tidal data, environmental variables have been collected for 3 hour intervals. Water velocity is used from those variables to determine its potential effect on detection performance.")

def clear_data():
    if st.button("Clear Previous Data"):
        subprocess.call(['sh', './reset_data.sh'])
        st.success("Data Cleared")


def load_processed_data(detections_file, detections_env_file):
    detection_df = pd.read_csv(detections_file)
    detection_env_df = pd.read_csv(detections_env_file)
    return detection_df, detection_env_df

def tidal_analysis():
    detections_file = "./data/streamlit-data/detections_data.csv"
    detections_env_file = "./data/streamlit-data/detections_data_env.csv"
    if os.path.isfile(detections_file) and os.path.isfile(detections_env_file):
        detection_df, detection_env_df = load_processed_data(detections_file, detections_env_file)
        st.subheader("Determine tidal heights via interpolation of tidal time tables")
        st.markdown("In addition to ocean and weather model data, historic tidal tables are available and used here to provide additional information about environmental cycles that could be factors of influence on the acoustic data.")

    else:
        st.error("""Uh oh! the required data files have not been generated, head over to the **load data** module""")

def editor():
    from streamlit_ace import st_ace
    yaml = st.sidebar.file_uploader("Upload Configuration YAML", type="yaml")
    yaml_content = ""
    if yaml is not None:
        yaml_content = yaml.read().decode('utf-8')
    content = st_ace(language = 'yaml', value=yaml_content)
    
    

def tracking():
    import kadlu
    st.subheader("Upload Raw Detection Data, Metadata & Vendor Tag Specifications")
    file1, file2, file3 = st.beta_columns(3)
    detections_data = file1.file_uploader("detections data")
    meta_data = file2.file_uploader("metadata")
    vendor_tag_specs = file3.file_uploader("Vendor Tag Specification")
    
    if detections_data is not None and meta_data is not None and vendor_tag_specs is not None:
        detections_data = io.BytesIO(detections_data.getbuffer())
        meta_data = io.BytesIO(meta_data.getbuffer())
        vendor_tag_specs = io.BytesIO(vendor_tag_specs.getbuffer())
        detection_df, mdb = at.read_otn_data(detections_data, meta_data, vendor_tag_specs, merge = True, bunch = True)
        if st.checkbox("Show Dataframe"):
            st.write(detection_df)

        #detection_df.to_csv("./data/streamlit-data/detections_data.csv")
        for field in ['Transmitter.Min delay', 'Transmitter.Max delay', 'Transmitter.Avg delay']:
            mdb.transmitter[field] = mdb.transmitter[field].max()
        df_dets, df_inits, rt_groups = at.process_intervals(detection_df, mdb)
        time_bin_len = 1*3600*at.sec1
        detection_df, event_bin_split = at.detection_rate_grid(df_dets, time_bin_len, mdb)
        events_df, bins_df = at.split_by_index(detection_df, event_bin_split)

        st.markdown("""### Detection data is merged with environmental variables from kadlu 
[Kadlu](https://docs.meridian.cs.dal.ca/kadlu/index.html#) is a Python package which provides functionality for fetching and interpolating environmental data related to ocean ambient nose levels. The `acoustic_tracking` package provides users with the option to integrate environmental data from Kadlu with their own detection datasets. To extract environmental data from kadlu, you will need to specify \n\n
(1) data sources\n
(2) bounds

Then, using these specifications you can use the `add_kadlu_env_data()` function to automatically extract and interpolate data using the kadlu Python package. """)
        
        st.subheader("Data Boundaries")
        st.markdown("""A bounds dictionary is used to specify the spatial and temporal boundaries for which you want to retrieve data. A `north`, `south`, `east`, and `west` value are provided to specify geospatial boundaries, while a `start` and `end` are used to specify temporal boundaries. Optionally, `top` and `bottom` values can be used to limit data to specific depths.""")

        st.sidebar.text("Please Choose your data source")
        is_chs = st.sidebar.checkbox('CHS')
        is_era5 = st.sidebar.checkbox('ERA5')
        is_gebco = st.sidebar.checkbox('GEBCO')
        is_hycom = st.sidebar.checkbox('HYCOM')
        is_wwiii = st.sidebar.checkbox('WWIII')


        bounds_data = dict()
        col1, col2 = st.beta_columns(2)
        with col1.beta_expander("Dates"):
            start_date = st.date_input("Start Date", datetime(2016, 3, 9))
            end_date = st.date_input("End Date", datetime(2016, 3, 11, 0))
            bounds_data['start'] = datetime(start_date.year, start_date.month, start_date.day)
            bounds_data['end'] = datetime(end_date.year, end_date.month, end_date.day)
        
        with col2.beta_expander("Coordinates"):
            bounds_data['lat'] = st.number_input("Enter the Latitude")
            bounds_data['lon'] = st.number_input("Enter the Longitude")
        
        with st.beta_expander("Offset"):
            north, south, east, west = st.beta_columns(4)
            bounds_data['north'] = bounds_data['lat'] + north.number_input("Enter the North Offset")
            bounds_data['south'] = bounds_data['lat'] - south.number_input("Enter the South Offset")
            bounds_data['east'] = bounds_data['lon'] + east.number_input("Enter the East Offset")
            bounds_data['west'] = bounds_data['lon'] - west.number_input("Enter the West Offset")

        bounds_data['top'], bounds_data['bottom'] = 0, 0
        if st.checkbox("Enable Debug Mode"):
            st.write(bounds_data)
        st.subheader("Map")
        st.markdown(""" Sometimes, it can be helpful to have a map visualization of the boundaries you are setting. Here, you can use the `plot_bounds` function to see the boundaries you have specified. Optionally, you can provide receiver locations and metadata to the `plot_bounds` function as well.""")

        m = render_map(bounds_data, detection_df)
        if st.checkbox("Render Map"):
            folium_static(m)
        
        st.subheader("Add Environmental Variables from Kadlu")
        df_detections_env = pd.DataFrame()
        if st.button("Load env data"):
            env_detections = at.add_kadlu_env_data(bounds_data, kadlu_sources, detection_df)
            st.write("Data after adding the environmental variables")
            env_detections.to_csv("./data/streamlit-data/detections_data_env.csv")
            st.write(env_detections)
        
        st.subheader("Reading Custom Data")
        st.markdown(""" In addition to integrating environmental data from Kadlu, acoustic_tracking allows you to integrate environmental data contained from custom NetCDF files. This allows users to leverage data from custom datasets which aren't available through Kadlu but might be relevant to the range test of interest. 
        
Here, we will use the `add_custom_env_data()` function to integrate custom environmental data from HYCOM with our detection dataset. This dataset provides finer resolution data for our region of interest than what is available through the Kadlu interface. """)
        
        if st.button("Load Custom HYCOM Data"):
            # df_detections_env = load_kadlu_data()
            axes_to_interpolate = [df_detections_env['Receiver.lat'], df_detections_env['Receiver.lon'], [d.timestamp() for d in df_detections_env['datetime']],df_detections_env['Receiver.depth']]
            data_dir = './data/HYCOM_20160309_20160404/'
            file_maps = {'salinity_bottom': '{}{}'.format(data_dir, 'bottom_sal_20160309_20160404_expt_56.3.nc'),
                'salinity': '{}{}'.format(data_dir, 'column_sal_20160309_20160404_expt_56.3.nc'),
                'water_v': '{}{}'.format(data_dir, 'column_v_vel_20160309_20160404_expt_56.3.nc'),
                'water_v_bottom': '{}{}'.format(data_dir, 'bottom_v_vel_20160309_20160404_expt_56.3.nc'),
                'surf_el': '{}{}'.format(data_dir, 'surf_el_20160309_20160404_expt_56.3.nc'),
                'water_temp_bottom': '{}{}'.format(data_dir, 'bottom_temp_20160309_20160404_expt_56.3.nc'),
                'water_temp': '{}{}'.format(data_dir, 'column_temp_20160309_20160404_expt_56.3.nc'),
                'water_u_bottom': '{}{}'.format(data_dir, 'bottom_u_vel_20160309_20160404_expt_56.3.nc'),
                'water_u': '{}{}'.format(data_dir, 'column_u_vel_20160309_20160404_expt_56.3.nc'),
                }
            df_detections_env = at.environment.add_custom_env_data(axes_to_interpolate, file_maps, df_detections_env)
            st.write(df_detections_env)

        st.subheader("We Save the newer dataframes for easier access")
        if st.button("Save Dataframes"):
            detection_df.to_csv("./data/streamlit-data/detections_data.csv")
            df_detections_env.to_csv("./data/streamlit-data/detections_data_env.csv")
            st.success("Successfully saved to disk")

            

def render_map(bounds, detection_df):
    

        receiver_info = detection_df[['Receiver.lat', 'Receiver.lon', 'Receiver.ID', 
                              'Receiver', 'Receiver.depth']].drop_duplicates()
        receiver_locations_df = detection_df[['Receiver.lat', 'Receiver.lon']].drop_duplicates()
        receiver_locations = list(zip(receiver_locations_df['Receiver.lat'], receiver_locations_df['Receiver.lon']))
        center = ((bounds['north'] + bounds['south'])/2, 
              (bounds['east'] + bounds['west'])/2)
        
        m = folium.Map(location=center, zoom_start=8)
        folium.Rectangle(bounds=((bounds['north'], bounds['east']), (bounds['south'], bounds['west'])), color='#ff7800', fill=True, fill_color='#ffff00', fill_opacity=0.1).add_to(m)
        tooltip = "Test"
        for lat, lon in receiver_locations:
            folium.Marker([lat,lon], popup="Sample Marker", tooltip=tooltip).add_to(m)

        
        return m


def load_discussion():
    st.title("Discussion")
    st.markdown(""" In the above visual summary, the **H-N** combinations, i.e. high-power, near distance, are the ones where water velocity shows the least effect on variations in detection rate (detection density). This confirms expectations and shows promise for the proposed study method. Next steps include:

- Continue to work with detection rate (DR) as calculated in a fixed grid of time windows
- Compare variations of DR with respect to other environmental variables
- Import other environmental variables automatically via data source APIs (ERDDAP, kadlu.fetch)
- Determine suitable numerical measure of factor importance in addition to visual analysis """)


def acknowledge():
    st.title("Acknowledgements")
    st.markdown("""The above analysis was performed using [data from OTN](http://members.devel.oceantrack.org/erddap/tabledap/otnunit_aat_detections.html) (provided by Jonathan Pye of OTN), in combination with HYCOM environmental data and tidal data provided by Casey Hilliard (Meridian/Dal), with a synthesized dataset prepared by Matthew Berkowitz (SFU), with project definition and guidance provided by Oliver Kirsebom (Dal) and Ines Hessler (Dal) as part of the [Meridian Network](https://meridian.cs.dal.ca).""")

def load_corr_data():
    return pd.read_csv("./data/detections_bin.csv")

def load_kadlu_data():
    return pd.read_csv("./data/streamlit-data/detections_data_env.csv")

def load_charts():
    st.title("Visualizations")
    st.header("Correlation Matrix")
    from acoustic_tracking.plotting import heatmaps
    det_df = load_corr_data()
    features = det_df[['wavedir', 'waveheight', 'waveperiod', 'salinity_bottom', 'salinity', 
                  'water_v', 'water_v_bottom', 'surf_el', 'water_temp_bottom', 'water_temp', 
                  'water_u_bottom', 'water_u', 't2', 'height', 'dheight_cm_per_hr', 'interval', 
                  'water_vel', 'detection_rate']]
                  
    correlation_method = st.sidebar.radio(
     'Correlation Method',
     ('spearman', 'pearson', 'kendall'))
    figure = heatmaps.plot_feature_heatmap(features, method=correlation_method)
    # w, h = st.beta_columns(2)
    # width = w.number_input("Enter Width")
    # height = h.number_input("Enter Height")
    # plt.rcParams["figure.figsize"] = width, height
    st.pyplot(figure)
    

if __name__ == "__main__":
    main()
