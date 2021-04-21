from pandas_ods_reader import read_ods
from .data_prep import *   # (process_intervals, detection_rate_grid)
from .data_prep import environment
from .dict_utils import *

class Detections:
    """ Manage detections: load, process, enhance, access """

    def __init__(self, config=None, do_processing=True):
        self.init_via_config(config)
        if do_processing:
            self.make_detection_rate()
            self.events_df, self.bins_df = self.get_events_bins(self.detection_df)
            self.prepare_rt_groups()
            self.add_env_data()
            self.add_custom_data()
            self.add_tidal_data()
            self.add_calculated_columns()
            self.prepare_group_data()

    def reset(self):
        self.config = None
        self.detection_df = None
        self.mdb = None
        self.df_dets = None
        self.df_inits = None
        self.event_bin_split = None
        self.events_df = None
        self.bins_df = None
        self.detection_env_df = None
        self.axes_to_interpolate = None
 
    def init_via_config(self, config):
        self.reset()
        self.config = config
        self.detection_df, self.mdb = read_via_config(self.config)

    def make_detection_rate(self):
        self.df_dets, self.df_inits, _ = process_intervals(self.detection_df,
                                                           self.mdb)
        self.detection_df, self.event_bin_split = detection_rate_grid(self.df_dets, 
                                                                      self.config.settings.time_bin_length,
                                                                      self.mdb,
                                                                      self.config.settings.auto_dr)
    
    @property
    def bounds(self):
        bounds_keys = ['north','south','east','west','top','bottom','start','end']
        return select_keys(self.config.bounds, bounds_keys)

    @property
    def sources(self):
        return self.config.data.sources

    @property
    def show_details(self):
        """Boolean to indicate whether details should be displayed"""
        return self.config.settings.show_details

    @property
    def node_locations(self):
        try:
            return set(list(zip(self.kadlu_result[1], self.kadlu_result[2])))
        except:
            return []

    @property
    def receiver_info(self):
        return self.mdb.receiver
    
    @property
    def receiver_locations(self):
        receiver_locations_df = self.receiver_info[['Receiver.lat', 'Receiver.lon']].drop_duplicates()
        return list(zip(receiver_locations_df['Receiver.lat'], receiver_locations_df['Receiver.lon']))

    def add_env_data(self):
        if self.sources:
            self.df_detections_env, self.kadlu_result = add_kadlu_env_data(self.bounds,
                                                                           self.sources,
                                                                           self.detection_df)
        else:
            self.df_detections_env = self.detection_df

    def add_custom_data(self):
        # Specify axes to interpolate (the axes which specify the points to interpolate)
        if 'file_map' in self.config.keys():
            self.axes_to_interpolate = [self.df_detections_env['Receiver.lat'],
                                        self.df_detections_env['Receiver.lon'],
                                        [d.timestamp() for d in self.df_detections_env['datetime']],
                                        self.df_detections_env['Receiver.depth']]
            # Add custom environment data
            self.df_detections_env = environment.add_custom_env_data(self.axes_to_interpolate, self.config.file_map, self.df_detections_env)

    def add_tidal_data(self):
        if 'tidal' in self.config.data.keys():
            self.df_tidal_times = read_ods(self.config.data.tidal.tidal_times_ods, 1)
            self.df_tidal_flat = flatten_tidal_table(self.df_tidal_times, year=self.config.data.tidal.year)
            self.df_tidal_interp = tidal_phase(self.df_tidal_flat, new_times = self.df_detections_env.datetime)
            self.df_detections_env = self.df_detections_env.reset_index().merge(
                self.df_tidal_interp[["t2","height","dheight_cm_per_hr"]], 
                how="left",
                left_on="datetime", right_index=True).set_index("index")

    def add_calculated_columns(self):
        if "calculated_columns" in self.config.data.keys():
            for colname in self.config.data.calculated_columns:
                make_column(self.df_detections_env, column_name=colname)

    def prepare_group_data(self):
        self.detection_events_df, self.detection_bins_df = self.get_events_bins(self.df_detections_env)
        self.rt_group_detections = list(self.df_detections_env.groupby(['Transmitter', 'Receiver']))

    def get_events_bins(self, df=None):
        if df is None:
            df = self.detection_env_df
        return split_by_index(df, self.event_bin_split)
    
    def prepare_rt_groups(self):
        deploy_lat_lon = self.mdb.deploy.groupby('STATION_NO')[['DEPLOY_LAT','DEPLOY_LONG']].nth(0)
        self.mdb.station_dists_m = calc_station_dists_m(deploy_lat_lon)
        if "Receiver/Transmitter" not in self.mdb.rt_groups.columns:
            add_rt_group_info(self.events_df, self.mdb)
