# ----------------------------------------------------------------------------
# geodesic distance calculation

from geopy.distance import geodesic

def dist_m(latlon0, latlon1):
    """Geodesic distance calculation"""
    return geodesic(latlon0, latlon1).m
