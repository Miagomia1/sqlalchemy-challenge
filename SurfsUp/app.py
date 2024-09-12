# Import the dependencies.
import numpy as np
import datetime as dt
import pandas as pd
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

#################################################
# Database Setup
engine = create_engine("sqlite:///hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
# Reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
app = Flask(__name__)

# Session handling
def get_session():
    return Session(engine)

#################################################
# Flask Routes
@app.route("/")
def welcome():
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

#################################################
# This route will return the last 12 months of precipitation data as JSON.

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = get_session()

    # Calculate the date 1 year ago from the last data point in the database
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    one_year_ago = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Perform the query to get the last 12 months of precipitation data
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()

    # Close the session
    session.close()

    # Create a dictionary with date as the key and precipitation as the value
    precip_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precip_dict)

#################################################
# This route will return the list of stations:

@app.route("/api/v1.0/stations")
def stations():
    session = get_session()

    # Query all stations
    results = session.query(Station.station).all()

    # Close the session
    session.close()

    # Convert list of tuples into a normal list
    stations_list = list(np.ravel(results))

    # Return JSON
    return jsonify(stations_list)

#################################################
# This route will return the temperature observations for the most active station for the last year:

@app.route("/api/v1.0/tobs")
def tobs():
    session = get_session()

    # Find the most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]

    # Calculate the date 1 year ago from the last data point
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    one_year_ago = dt.datetime.strptime(most_recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query the temperature observations for the last year
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago).all()

    # Close the session
    session.close()

    # Create a list of dictionaries
    temps_list = [{date: temp} for date, temp in results]

    # Return JSON
    return jsonify(temps_list)

#################################################
# Routes: /api/v1.0/<start> and /api/v1.0/<start>/<end>
# These routes will return the min, avg, and max temperatures for a given start date, or a start-end range.

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    session = get_session()

    # If there's no end date, set the end date to the most recent date
    if not end:
        end = session.query(func.max(Measurement.date)).scalar()

    # Query for min, avg, max temperatures for the date range
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()

    # Close the session
    session.close()

    # Convert the query result to a list of dictionaries
    temps_data = [{"TMIN": result[0], "TAVG": result[1], "TMAX": result[2]} for result in results]

    # Return JSON
    return jsonify(temps_data)

#################################################
# Run the Flask app:
if __name__ == "__main__":
    app.run(debug=True)








