export type Site = {id:string;name:string;latitude:number;longitude:number;altitude_km:number};
export type Sample = {time:string;sun_azimuth_deg:number;sun_elevation_deg:number;earth_azimuth_deg:number;earth_elevation_deg:number;solar_power_w_ideal:number;sunlit_geometric:boolean;earth_visible_geometric:boolean;simultaneous_window:boolean};
export type Result = {site:Site;series:Sample[];summary:{samples:number;solar_availability_percent:number;earth_visibility_percent:number;simultaneous_availability_percent:number;mean_ideal_power_w_when_sampled:number};source:string;caveats:string[]};
