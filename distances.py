'''
Traveling Baseball Fan Problem
Author: Sertalp B. Cay

Distances between MLB stadiums
'''

import requests
import io
import pandas as pd
import glob
from concurrent.futures import ThreadPoolExecutor
from itertools import cycle


def get_distances():
    team_data = pd.read_csv('data/team_list.txt', sep='\t', header=None, names=['ID', 'City', 'Team', 'Venue'])
    team_data['Address'] = team_data['Venue'] + ' ' + team_data['City']
    addresses = team_data['Address'].tolist()

    # Part 1 - Get Coordinates
    def get_coordinate(address):
        r = requests.get('https://nominatim.openstreetmap.org/search?q={}&format=json'.format(address))
        if r.status_code == 200:
            coords = (r.json()[0]['lat'], r.json()[0]['lon'])
            print(address, coords)
            return coords
        return None

    coords = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        responses = executor.map(get_coordinate, addresses)
        coords = [r for r in responses]

    team_data['Coords'] = pd.Series(coords)
    team_data['lat'] = team_data['Coords'].str[1]
    team_data['lon'] = team_data['Coords'].str[0]
    team_data.to_csv('data/coords.csv')

    # Part 2 - Get travel time
    coord_full_list = ';'.join(str(i[1]) + ',' + str(i[0]) for i in team_data['Coords'].tolist())
    r = requests.get('http://router.project-osrm.org/table/v1/driving/{}'.format(coord_full_list))

    # Part 3 - Get distance
    combinations = []
    for i, source in enumerate(team_data['Coords']):
        for j, dest in enumerate(team_data['Coords']):
            combinations.append('http://router.project-osrm.org/route/v1/driving/{},{};{},{}?overview=false'.format(source[1], source[0], dest[1], dest[0]))

    def get_distances(url):
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()['routes'][0]['distance'] * 0.000621371  # Meter to Mile

    distances = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        distances = executor.map(get_distances, combinations)

    # Create data
    dist_cycle = cycle(distances)
    distance_matrix = []
    if r.status_code == 200:
        dist = r.json()['durations']
        for i, row in enumerate(dist):
            for j, val in enumerate(row):
                distance_matrix.append([i+1, j+1, team_data.at[i, 'Venue'], team_data.at[j, 'Venue'], val/60.0, next(dist_cycle)])

    for i in distance_matrix:
        print(i)
    # Write to file
    df = pd.DataFrame(distance_matrix, columns=['stad1', 'stad2', 'name', 'name2', 'minutes', 'miles'])
    df.to_csv('data/distance.csv')


if __name__ == '__main__':
    get_distances()