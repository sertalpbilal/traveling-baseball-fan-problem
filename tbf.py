'''
Traveling Baseball Fan Problem
Author: Sertalp B. Cay

This file contains the pre-processing of MLB season schedule and the Python
implementation of the Traveling Baseball Fan Problem (TBFP).

The parse_data function pre-processes the distance data, reads the home
schedule of every team and returns all the information.

The tbfp function takes these inputs, prepare the optimization problem and
pass it to the SAS Viya Mixed-Integer Optimization solver and parses the result.
Users can visualize the resulting schedule using folium package.
'''

import pandas as pd
import glob
import data
import numpy as np
import sasoptpy as so
from swat import CAS
import datetime
from dateutil import relativedelta
import time
from osm import get_driving_times


def parse_data():

    # Read the distance data and fix name differences
    distance_data = pd.read_csv('data/distance.csv', quoting=1)
    distance_data.columns = [i.replace('\'','') for i in distance_data.columns.tolist()]
    distance_data = distance_data.replace('\'', '', regex=True)
    distance_data = distance_data.replace('OAC Coliseum', 'Oakland Coliseum')
    distance_data = distance_data.replace('PETCO Park', 'Petco Park')
    distance_data = distance_data.replace('Angels Stadium of Anaheim', 'Angel Stadium of Anaheim')
    distance_data = distance_data.replace('ATT Park', 'AT&T Park')
    distance_data = distance_data.set_index(['name', 'name.1'])
    driving_data = get_driving_times()
    game_data = pd.DataFrame()
    venue_data = pd.read_csv('data/geocode.csv').set_index('venue')

    # Read schedules of all MLB teams
    for tfile in glob.glob('data/t*.csv'):
        csvdata = pd.read_csv(tfile, usecols=['START DATE', 'START TIME ET', 'END DATE ET', 'END TIME ET', 'SUBJECT', 'LOCATION'])
        game_data = game_data.append(csvdata)

    # Set data types and filter out missing games
    game_data = game_data.dropna(subset=['START TIME ET'])
    game_data = game_data.sort_values(by=['START DATE', 'START TIME ET', 'SUBJECT'])
    game_data = game_data.reset_index(drop=True)

    # Parse game data
    game_data[['AWAY', 'HOME']] = game_data.pop('SUBJECT').str.split(' at ', expand=True)
    game_data[['VENUE', 'CITY']] = game_data.pop('LOCATION').str.split(' - ', expand=True)
    game_data['HOME'] = game_data['HOME'].replace('D-backs', 'Diamondbacks')
    game_data['AWAY'] = game_data['AWAY'].replace('D-backs', 'Diamondbacks')
    game_data['START'] = pd.to_datetime(game_data.pop('START DATE') + ' ' + game_data.pop('START TIME ET'), format='%m/%d/%y %I:%M %p')
    game_data['END'] = pd.to_datetime(game_data.pop('END DATE ET') + ' ' + game_data.pop('END TIME ET'), format='%m/%d/%y %I:%M %p')
    game_data = game_data[game_data['START'] >= pd.Timestamp('20180329')]

    print('Parsed all data...')
    return(distance_data, driving_data, game_data, venue_data)


'''
Defines the optimization problem and solves it.

Parameters
----------
distance_data : pandas.DataFrame
    Distances between stadiums in miles.
driving_data : pandas.DataFrame
    The driving times between stadiums in minutes.
game_data : pandas.DataFrame
    The game schedule information for the current season.
venue_data : pandas.DataFrame
    The information regarding each 30 MLB venues.
start_date : datetime.date, optional
    The earliest start date for the schedule.
end_date : datetime.date, optional
    The latest end date for the schedule.
obj_type : integer, optional
    Objective type for the optimization problem,
    0: Minimize total schedule time, 1: Minimize total cost
'''
def tbfp(distance_data, driving_data, game_data, venue_data,
         start_date=datetime.date(2018, 3, 29),
         end_date=datetime.date(2018, 10, 31),
         obj_type=0):

    # Define a CAS session
    cas_session = CAS(your_cas_server, port=your_cas_port)
    m = so.Model(name='tbfp', session=cas_session)

    t0 = time.time()
    # Discard games outside of the selected interval
    game_data = game_data[game_data['START'] >= start_date]
    game_data = game_data[game_data['END'] <= end_date]

    # Define sets
    STADIUMS = sorted(venue_data.index.tolist())
    game_data = game_data[game_data['VENUE'].isin(STADIUMS)]
    GAMES = game_data.index.tolist()
    NODES = GAMES + ['source', 'sink']

    # Define parameters
    away = game_data['AWAY']
    home = game_data['HOME']
    start = game_data['START']
    end = game_data['END']
    location = game_data['VENUE']
    city = game_data['CITY']
    driving = driving_data['duration']
    distance = distance_data['dist1']
    lat = venue_data['lat']
    lon = venue_data['lon']

    min_dist = {s: 0 for s in STADIUMS}
    arg_min = {s: 0 for s in STADIUMS}

    print('Numer of GAMES: {}'.format(len(GAMES)))

    # Define all possible arcs in the network model
    ARCS = []
    for g1 in GAMES:
        for s in STADIUMS:
            min_dist[s] = datetime.datetime(2019,1,1)
            arg_min[s] = -1
        for g2 in GAMES:
            if location[g1] != location[g2]:
                time_between = driving[location[g1], location[g2]]
                driving_time = datetime.timedelta(minutes = float(time_between))
                if end[g1] + driving_time <= start[g2] and min_dist[location[g2]] > start[g2]:
                    min_dist[location[g2]] = start[g2]
                    arg_min[location[g2]] = g2
        for s in STADIUMS:
            if arg_min[s] != -1:
                ARCS.append((g1, arg_min[s]))

    ARCS = ARCS + [('source',g) for g in GAMES] + [(g,'sink') for g in GAMES]
    print('Number of ARCS: {}'.format(len(ARCS)))

    cost = {}
    for (g1,g2) in ARCS:
        if g1 != 'source' and g2 != 'sink':
            cost[g1,g2] = (end[g2] - end[g1]).total_seconds()/86400.0
        elif g2 != 'sink' and g1 == 'source':
            cost[g1,g2] = (end[g2]-start[g2]).total_seconds()/86400.0
        else:
            cost[g1,g2] = 0

    t1 = time.time()
    data_time = t1-t0

    # Add variables
    use_arc = m.add_variables(ARCS, vartype=so.BIN, name='use_arc')

    # Define expressions for the objectives
    total_time = so.quick_sum(
        cost[g1,g2] * use_arc[g1,g2] for (g1, g2) in ARCS)
    total_distance = so.quick_sum(
        distance[location[g1], location[g2]] * use_arc[g1, g2]
        for (g1, g2) in ARCS if g1 != 'source' and g2 != 'sink')
    total_cost = total_time * 130 + total_distance * 0.25

    # Set objectives
    if obj_type == 0:
        m.set_objective(total_time, sense=so.MIN)
    elif obj_type == 1:
        m.set_objective(total_cost, sense=so.MIN)

    # Balance constraint
    m.add_constraints((
        so.quick_sum(use_arc[g, g2] for (gx,g2) in ARCS if gx==g) -\
        so.quick_sum(use_arc[g1, g] for (g1,gx) in ARCS if gx==g)\
        == (1 if g == 'source' else (-1 if g == 'sink' else 0) )
        for g in NODES),
        name='balance')

    # Visit once constraint
    visit_once = so.ConstraintGroup((
        so.quick_sum(
            use_arc[g1,g2]
            for (g1,g2) in ARCS if g2 != 'sink' and location[g2] == s) == 1
        for s in STADIUMS), name='visit_once')
    m.include(visit_once)

    prep_mark = time.time()
    prep_time = prep_mark - t1
    # Send the problem to SAS Viya solvers and solve the problem
    m.solve(milp={'concurrent': True})

    solve_time = time.time() - prep_mark
    

    # Parse the results
    schedule = []
    for (g1,g2) in ARCS:
        if (use_arc[g1,g2].get_value() > 0.5 and 
            g1 != 'source' and g2 != 'sink'):
            if g1 not in schedule:
                schedule.append(g1)
            if g2 not in schedule:
                schedule.append(g2)

    # Sort the schedule and print information
    schedule = sorted(schedule, key=lambda i: start[i])
    route = []
    shortest_dist = [distance[location[schedule[0]],
                              location[schedule[1]]], 1, 2]
    longest_dist = shortest_dist
    shortest_time = [
        (start[schedule[1]] - end[schedule[0]]).total_seconds() / 60.0, 1, 2]
    longest_time = shortest_time
    most_critical = [shortest_time[0] - shortest_dist[0], 1, 2]
    c_game = -1
    print('{:3} {:<30} {:<12} {:<12} {:<20} {:<19} {:<6} {:<6}'.format(
        'Obs', 'Location', 'Away', 'Home', 'City', 'Time', 'Lat', 'Lon'))
    for i, g in enumerate(schedule):
        route.append([i+1, location[g], away[g], home[g], city[g], start[g],
                      lat[location[g]], lon[location[g]]])
        print('{:3d} {:<30} {:<12} {:<12} {:<20} {} {:6.3f} {:6.3f}'.format(
            *route[-1]))
        if c_game != -1:
            c_dis = distance[location[c_game], location[g]]
            c_driv = driving[location[c_game], location[g]]
            c_tim = (start[g] - end[c_game]).total_seconds() / 60.0
            if c_dis > longest_dist[0]:
                longest_dist = [c_dis, i, i+1]
            if c_dis < shortest_dist[0]:
                shortest_dist = [c_dis, i, i+1]
            if c_tim > longest_time[0]:
                longest_time = [c_tim, i, i+1]
            if c_tim < shortest_time[0]:
                shortest_time = [c_tim, i, i+1]
            if c_tim - c_driv < most_critical[0]:
                most_critical = [c_tim - c_driv, i, i+1]
        c_game = g

    print('Total time: {}'.format(end[schedule[-1]] - start[schedule[0]]))
    
    # Optional, plot results
    if False: # disabled
        from map import plot_tbf
        plot_tbf(route, name=str(id(m)))

    # Save the resulting schedules and information into a file for notebook
    n_months = (end_date-start_date).total_seconds()/(60.0*60.0*24*30)
    out = '''objt: {}
sdat: {}
edat: {}
mont: {:.1f}
time: {:.3f} days
dist: {:.3f} miles
cost: {:.3f} USD
gams: {}
vars: {}
cons: {}
data: {:.3f} secs
prep: {:.3f} secs
solv: {:.3f} secs
sdis: {} {}-{}
ldis: {} {}-{}
stim: {} {}-{}
ltim: {} {}-{}
mcri: {} {}-{}
schd: [
'''.format(obj_type, start_date, end_date, n_months,
           total_time.get_value(), total_distance.get_value(),
           total_cost.get_value(),
           len(GAMES), len(m.get_variables()), len(m.get_constraints()),
           data_time, prep_time, solve_time,
           *shortest_dist, *longest_dist, *shortest_time, *longest_time,
           *most_critical)
    out += '{}'.format('\n'.join([','.join([str(j) for j in i])
                                  for i in route]))
    out += '\n]'
    file = open('results/{}.txt'.format(id(m)), 'w')
    file.write(out)
    file.close()
    print(out)


'''
Run all the experiments for the blog post
'''
def experiments():
    distance_data, driving_data, game_data, venue_data = parse_data()
    date_range = [
        [datetime.date(2018,3,29), datetime.date(2018,6,1)],
        [datetime.date(2018,6,1), datetime.date(2018,8,1)],
        [datetime.date(2018,8,1), datetime.date(2018,10,1)],
        [datetime.date(2018,3,29), datetime.date(2018,7,1)],
        [datetime.date(2018,7,1), datetime.date(2018,10,1)],
        [datetime.date(2018,3,29), datetime.date(2018,10,1)]
        ]
    obj_type = [0, 1]
    for d in date_range:
        for o in obj_type:
            tbfp(distance_data, driving_data, game_data, venue_data,
                 start_date=d[0], end_date=d[1], obj_type=o)
            so.reset_globals()

if __name__ == '__main__':
    experiments()

