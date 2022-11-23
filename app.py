# Import dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import datetime as dt

# Set up database.
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model.
Base = automap_base()
# Reflect the tables.
Base.prepare(engine, reflect=True)

# Save reference to the tables.
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create an app.
app = Flask(__name__)

# Define what to do when a user hits the Home route.
@app.route("/")
def welcome():
    """Homepage. 
    List all available routes."""
    return (
        """<h1>Welcome to my Climate App!</h1>
            You are currently viewing the Home page.
        <h2>Base API</h2>
            The base API route is: <code>/api/v1.0/</code>
        <h2>Available API Routes</h2>
            Here are the available API routes:<br>
            <li><code>/api/v1.0/precipitation</code>: <small>View the JSON list of dates and precipitation values.</small></li>
            <li><code>/api/v1.0/stations</code>: <small>View the JSON list of stations.</small></li>
            <li><code>/api/v1.0/tobs</code>: <small>View the JSON list of temperature observations (TOBS) of the most active station for the previous year.</small></li>
            <li><code>/api/v1.0/&ltstart&gt/&ltend&gt</code>: <small>View the JSON list of minimum, average, and maximum temperature for a given start or start-end range. Start and/or end dates must be formatted as "YYYY-MM-DD".</small></li>"""
    )

# Define what to do when a user hits the /api/v1.0/precipitation route.
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Convert the query results to a dictionary using date as the key and prcp as the value.
    Return the JSON representation of your dictionary."""
     # Create our session (link) from Python to the DB.
    session = Session(engine)

    """Return a list of dates and precipitation data."""
    # Query precipitation data.
    results = session.query(Measurement.date, Measurement.prcp).all()

    session.close()
    
    # Create a dictionary from the row data and append to a list of all_precipitation.
    all_precipitation = []
    for date, prcp in results:
        precipitation_dict = {}
        precipitation_dict["date"] = date
        precipitation_dict["precipitation"] = prcp
        all_precipitation.append(precipitation_dict)

    return jsonify(all_precipitation)

# Define what to do when a user hits the /api/v1.0/stations route.
@app.route("/api/v1.0/stations")
def stations():
    "Return a JSON list of stations from the dataset."
     # Create our session (link) from Python to the DB.
    session = Session(engine)

    """Return a list of station data."""
    # Query all stations.
    results = session.query(Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()

    session.close()
    
    # Create a dictionary from the row data and append to a list of all_stations.
    all_stations = []
    for station, name, latitude, longitude, elevation in results:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        all_stations.append(station_dict)

    return jsonify(all_stations)

# Define what to do when a user hits the /api/v1.0/tobs route.
@app.route("/api/v1.0/tobs")
def tobs():
    """Query the dates and temperature observations of the most active station for the previous year of data. 
    Return a JSON list of temperature observations (TOBS) for the previous year."""
     # Create our session (link) from Python to the DB.
    session = Session(engine)

    """Return a list of tobs data."""
    # Query all tobs.
    active_station = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()
    last_dt = session.query(func.max(Measurement.date)).filter(Measurement.station==active_station[0]).order_by(Measurement.date.desc()).first()
    query_dt = dt.datetime.strptime(last_dt[0], '%Y-%m-%d').date()-dt.timedelta(days=365)
    results = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station==active_station[0], Measurement.date>=query_dt).all()
    
    session.close()
    
    # Create a dictionary from the row data and append to a list of all_tobs.
    all_tobs = []
    for date, tobs in results:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)

# Define what to do when a user hits the /api/v1.0/<start>/<end> route
@app.route("/api/v1.0/<start>", defaults={"end": None})
@app.route("/api/v1.0/<start>/<end>")
def min_avg_max_tob(start, end):
    """Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a given start or start-end range.
    When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than or equal to the start date.
    When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates from the start date through the end date (inclusive)."""

    # Create our session (link) from Python to the DB.
    session = Session(engine)

    """Return a list of tobs data."""
    # Query tobs with provided start and/or end dates.
    start_dt = dt.datetime.strptime(start, '%Y-%m-%d').date()
    if end == None:
        last_dt = session.query(func.max(Measurement.date)).order_by(Measurement.date.desc()).first()
        last_dt = dt.datetime.strptime(last_dt[0], '%Y-%m-%d').date()
    else:
        last_dt = dt.datetime.strptime(end, '%Y-%m-%d').date()
    
    min_temp = session.query(func.min(Measurement.tobs)).filter(Measurement.date>=start_dt, Measurement.date<=last_dt).first()
    avg_temp = session.query(func.avg(Measurement.tobs)).filter(Measurement.date>=start_dt, Measurement.date<=last_dt).first()
    max_temp = session.query(func.max(Measurement.tobs)).filter(Measurement.date>=start_dt, Measurement.date<=last_dt).first()
    
    session.close()

    temp_dict = [
        {'tmin': min_temp[0], 'tavg': avg_temp[0], 'tmax': max_temp[0]}
    ]
    return jsonify(temp_dict)

if __name__ == "__main__":
    app.run(debug=True)