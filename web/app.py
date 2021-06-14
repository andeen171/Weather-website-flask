from sqlalchemy.exc import IntegrityError
from flask import Flask, render_template, request, redirect, flash
from datetime import datetime, time, timedelta
from flask_sqlalchemy import SQLAlchemy
import sys
import requests

app = Flask(__name__)
app.secret_key = ''
api_key = ''
early = time(5, 0, 0)
morning = time(6, 0, 0)
nightfall = time(17, 0, 0)
night = time(19, 0, 0)

# ============= DATABASE ===============
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'


class City(db.Model):
    __events__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR, nullable=False, unique=True)


db.create_all()


# ============= PROCESSING ===============
def GetTemp(city):
    response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city.name}&appid={api_key}')
    temp = response.json()['main']['temp'] - 273.15
    desc = response.json()['weather'][0]['description']
    timeShift = response.json()['timezone'] / 3600
    tempo = GetTimeOfDay(timeShift)
    return {'temp': round(temp, 1), 'desc': desc.title(), 'time': tempo, 'name': city.name, 'id': city.id}


def GetTimeOfDay(timeShift):
    if '-' in str(timeShift):
        timeShift = timeShift * -1
        hour = datetime.utcnow() - timedelta(hours=timeShift)
    else:
        hour = datetime.utcnow() + timedelta(hours=timeShift)
    if morning < hour.time() < nightfall:
        return "day"
    elif hour.time() > night or hour.time() < early:
        return "night"
    else:
        return "evening-morning"


def SetCityList():
    list_ = []
    cities = City.query.all()
    for i in cities:
        list_.append(GetTemp(i))
    return list_


# ============= ROUTES ===============
@app.route('/')
def index():
    list_ = SetCityList()
    return render_template('index.html', weather=list_)


@app.route('/add', methods=['POST'])
def add_city():
    city_name = request.form.get('city_name')
    city = City(name=city_name)
    response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}')
    if response.json()['cod'] == '404':
        flash("The city doesn't exist!")
    else:
        try:
            db.session.add(city)
            db.session.commit()
        except IntegrityError:
            flash('The city has already been added to the list!')
    return redirect('/')


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete_city(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
