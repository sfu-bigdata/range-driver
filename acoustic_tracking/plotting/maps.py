import pandas as pd
from ipyleaflet import Map, Rectangle, Marker, MarkerCluster, AwesomeIcon, Popup
from ipywidgets import HTML
from IPython.display import display


def plot_bounds(bounds, receiver_locations=[], receiver_info=pd.DataFrame(), node_locations=[]):
    """
    Construct a map view widget for the given region with further info. The map widget displays
    inside IPython notebooks.

    :param bounds: Dictionary containing the keys 'north', 'east', 'south', 'west'. Each value
                   should be a latitude or longitude in degrees.
    :type bounds: dict

    :param receiver_locations: List of tuples containing the locations (lat, lon) of receivers.
    :type receiver_locations: list

    :param receiver_info: A dataframe containing receiver information to be displayed on the map.
    :type receiver_info: pandas.DataFrame

    :param node_locations: Set of tuples containing the locations (lat, lon) of data nodes.
    :type node_locations: set
    """
    # Create the Map
    # **************
    center = ((bounds['north'] + bounds['south'])/2, 
              (bounds['east'] + bounds['west'])/2)
    m = Map(center=center, zoom=8)

    # Add a rectagle for the Bounds
    # *****************************
    rectangle = Rectangle(bounds=((bounds['north'], bounds['east']), 
                                  (bounds['south'], bounds['west'])), 
                          color='#2e4053', opacity=0.5, weight=3,
                          fill_color='#2e4053', fill_opacity=0.1)
    m.add_layer(rectangle)
    
    # Add markers for Receiver Locations
    # **********************************
    receiver_markers = []
    for lat, lon in receiver_locations:
        # Create Icon for the Marker
        icon = AwesomeIcon(name='microphone', 
                           marker_color='darkblue')
        
        # Create Popup message
        if receiver_info is not None:
            r_info = receiver_info[(receiver_info['Receiver.lat']==lat) &
                                   (receiver_info['Receiver.lon']==lon)]
            r_info = r_info.drop(['Receiver.lat', 'Receiver.lon'], axis=1)
        message = HTML()
        message.value = r_info.to_html(index=False)
        
        # Add Marker
        receiver_markers.append(Marker(location=(lat, lon), 
                                       draggable=False, 
                                       icon=icon, 
                                       popup=message))
    # Group the markers into a cluster
    receiver_cluster = MarkerCluster(markers=receiver_markers)
    # Add marker cluster to the map
    m.add_layer(receiver_cluster)
         
    # Add markers for Node Locations
    # ******************************
    node_markers = []
    for lat, lon in node_locations:
        # Create Icon for the Marker
        icon = AwesomeIcon(name='info', 
                           marker_color='lightred')
        
        # Add Marker
        node_markers.append(Marker(location=(lat, lon), 
                                   draggable=False, 
                                   icon=icon, 
                                   size=10, 
                                   opacity=0.8))
    
    node_cluster = MarkerCluster(markers=node_markers)
    # Add marker cluster to the map
    m.add_layer(node_cluster)

    # Display the map
    # ***************

    display(m)
    return m