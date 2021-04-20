import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, text

from flask import Flask, jsonify

MAX_DATE = "9999-12-31"
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()
Base.prepare(engine, reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station

app = Flask(__name__)

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations</br>"
        f"/api/v1.0/tobs</br>"
        f"/api/v1.0/&lt;start&gt; and /api/v1.0/&lt;start&gt;/&lt;end&gt; (&lt;start&gt; & &lt;end&gt; are dates in the format '%Y-%m-%d' (ex 2016-12-31)"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    latest_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()._asdict()['date']
    latest_date_dt = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    year_from_last = latest_date_dt - dt.timedelta(days=365)
    results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= year_from_last).all()

    session.close()

    measurement_dict = {}
    for date, prcp in results:
        measurement_dict[date] = prcp

    return jsonify(measurement_dict)


@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)

    results = session.query(Station.name).all()

    session.close()

    all_stations = list(np.ravel(results))

    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    most_active = session.query(Measurement.station, func.count(Measurement.station).label('total')).group_by(Measurement.station).order_by(text('total DESC')).first()[0]
    latest_date = session.query(Measurement.date).filter(Measurement.station == most_active).order_by(Measurement.date.desc()).first()._asdict()['date']
    latest_date_dt = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    year_from_last = latest_date_dt - dt.timedelta(days=365)
    data = session.query(Measurement.tobs, Measurement.date).\
      filter(Measurement.date >= year_from_last, Measurement.station == most_active).\
      order_by(Measurement.date.desc()).all()

    session.close()
    
    measurement_dict = {}
    for tobs, date in data:
        measurement_dict[date] = tobs

    return jsonify(measurement_dict)

@app.route("/api/v1.0/<start>", defaults={"end": MAX_DATE})
@app.route("/api/v1.0/<start>/<end>")
def dates(start, end):
    # end = end or "9999-12-31" #dt.datetime.datetime.strftime(dt.datetime.utcnow(), "%Y-%m-%d")
    try:
      dt.datetime.strptime(start, "%Y-%m-%d")
      dt.datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
      return("Enter a valid date in format '%Y-%m-%d' (ex. 2016-12-31)")
    if start > end:
      return("Start date cant be after end date")
    session = Session(engine)
    stats = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).filter(Measurement.date >= start, Measurement.date <=  end).first()
    session.close()
    print(f'stats {stats}')
    if not stats[0]:
      return('no results')
    else:
      stats_dict = {
        'min_temp': stats[0],
        'avg_temp': round(stats[1]),
        'max_temp': stats[2]
      }
      return jsonify(stats_dict)


if __name__ == '__main__':
    app.run(debug=True)
