# Getting OSM driving times
import pandas as pd
import requests
import json

'''
This function gets driving times between stadiums from OpenStreetMap.
See more at http://project-osrm.org/
'''
def get_driving_times():
    geocodes = pd.read_csv('data/geocode.csv')
    venues = geocodes['venue'].tolist()
    
    coords = ['{:.4f},{:.4f}'.format(i['lon'], i['lat']) for _,i in geocodes.iterrows()]
    coord_s = ';'.join(coords)
    
    osm_url = 'http://router.project-osrm.org/table/v1/driving/{}'.format(coord_s)
    r = requests.get(osm_url)
    r_dict = json.loads(r.text)
    durations = r_dict['durations']
    
    distance_table = []
    
    for i, v1 in enumerate(venues):
        for j, v2 in enumerate(venues):
            distance_table.append([v1, v2, durations[i][j]/60.0])
    
    df = pd.DataFrame(distance_table, columns=['v1', 'v2', 'duration']).set_index(['v1', 'v2'])
    return df

get_driving_times()