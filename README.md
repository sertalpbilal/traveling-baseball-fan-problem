# Traveling Baseball Fan Problem

Repository for the Traveling Baseball Fan Problem (TBFP).
See the [SAS/OR blog post](https://blogs.sas.com/content/operations/2018/06/13/visiting-all-30-major-league-baseball-stadiums-with-python-and-sas-viya/) for details.

## Repository structure

### Files

- TBFP.ipynb: Jupyter notebook for visualizations. See it at [NBviewer](http://nbviewer.jupyter.org/github/sertalpbilal/traveling-baseball-fan-problem/blob/master/TBFP.ipynb).
- data.py: Python script for scrapping MLB season schedule from MLB website.
- osm.py: Python script for scraping driving distances between stadiums from OpenStreetMap (OSRM) test server.
- tbf.py: Python script for pre-processing the data, modeling the TBFP and solving it with Viya MILP solvers.
- map.py: Python script for exporting a solution into an interactive Leaflet map using OpenStreetMap data.

### Folders

- data: Includes game schedule downloaded from MLB.com, distances between venues and their geocodes.
- results: Includes txt files to describe optimization problems results.
- maps: Includes html pages to display solutions on interactive Leaflet maps.

## Optimal solutions

### All results

![https://blogs.sas.com/content/operations/files/2018/06/all_solutions.png](https://blogs.sas.com/content/operations/files/2018/06/all_solutions.png)

### 2018 season

#### Shortest tour possible

![https://blogs.sas.com/content/operations/files/2018/06/map11.png](https://blogs.sas.com/content/operations/files/2018/06/map11.png)

![https://blogs.sas.com/content/operations/files/2018/06/sched11.png](https://blogs.sas.com/content/operations/files/2018/06/sched11.png)

#### Cheapest tour after the midseason classic

![https://blogs.sas.com/content/operations/files/2018/06/map10.png](https://blogs.sas.com/content/operations/files/2018/06/map10.png)

![https://blogs.sas.com/content/operations/files/2018/06/sched10.png](https://blogs.sas.com/content/operations/files/2018/06/sched10.png)
