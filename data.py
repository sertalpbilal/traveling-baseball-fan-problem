'''
Traveling Baseball Fan Problem
Author: Sertalp B. Cay

This file can be used for grabbing the MLB season schedule from the MLB.com
website. MLB.com provides season schedule in CSV format which is used here.

Driving distances are obtained from mlb-stadiums repository:
https://bitbucket.org/trhdata/mlb-stadiums/src

Team codes (for MLB.com) is obtained from:
https://github.com/BenDrozdoff/bts_2018
'''

import requests
import io
import pandas as pd

teams = {
    'Rockies': 115,
    'Cardinals': 138,
    'Athletics': 133,
    'Angels': 108,
    'Blue Jays': 141,
    'Astros': 117,
    'Pirates': 134,
    'Mets': 121,
    'White Sox': 145,
    'Phillies': 143,
    'Royals': 118,
    'Twins': 142,
    'Padres': 135,
    'Braves': 144,
    'Nationals': 120,
    'Rangers': 140,
    'Cubs': 112,
    'Reds': 113,
    'Tigers': 116,
    'Yankees': 147,
    'Mariners': 136,
    'Giants': 137,
    'Marlins': 146,
    'Indians': 114,
    'Dodgers': 119,
    'Rays': 139,
    'Brewers': 158,
    'Orioles': 110,
    'Red Sox': 111,
    'Diamondbacks': 109,
    'Marlins': 146
    }


'''
This function grabs the associated CSV file for each team.
CSV file contains home games of the team.
We write all CSV files under data/ folder.
'''
def get_team_schedule(team_id, team_name):
    print('Grabbing schedule: {}'.format(team_name))
    url = 'http://www.ticketing-client.com/ticketing-client/csv/EventTicketPromotionPrice.tiksrv?team_id={team}&home_team_id={team}&display_in=singlegame&ticket_category=Tickets&site_section=Default&sub_category=Default&leave_empty_games=true&event_type=T'
    r = requests.get(url.format(team=team_id))
    if r.status_code == 200:
        content = r.content.decode('utf-8')
        filename = 'data/t{}_{}.csv'.format(team_id, str(team_name).replace(' ',''))
        csv = open(filename, 'w')
        csv.write(content)
        print('Schedule is written: {}'.format(filename))


if __name__ == '__main__':
    for name, id in teams.items():
        get_team_schedule(id, name)

