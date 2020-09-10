from flask import Flask, render_template, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import configure_uploads, IMAGES, UploadSet
from forms import RegistrationForm, LoginForm, LocationForm
from datetime import datetime
import re
from ocr_preprocess import preprocessing
from ocr_process import processing
import os 
import requests
from requests.exceptions import HTTPError
import json 

app = Flask(__name__)
app.config['SECRET_KEY'] = '5ade19333b2a3398779e37bf1f92d6fa'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOADED_IMAGES_DEST'] = './imgtxtenh'

images = UploadSet('images', IMAGES)
configure_uploads(app, images)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')   
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
    
posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]

@app.route('/')
@app.route('/maps', methods=['GET', 'POST'])
def maps():
    form = LocationForm()
    if form.validate_on_submit():
        coors = [re.sub(r' ','\+',str(form.x_coor.data)), re.sub(r' ','\+',str(form.y_coor.data))]
        # print(form.image)
        file_name = images.save(form.image.data)
        # print('Prepocessing')
        preprocessing(file_name)
        # print('Done')
        # print('Processing')
        # print(form.crs.data)
        coors = list(processing(file_name, int(form.crs.data)))
        # print('Done')
        os.remove(f'./imgtxtenh/{file_name}')
        os.remove(f'./imgtxtenh/pre_{file_name}')
        try:
            response = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?latlng={coors[0]},{coors[1]}&key=AIzaSyCaRkfQYahP3fTIL31Da9Ppv5rnNWcG1F0')
            # access JSOn content
            jsonResponse = response.json()
            coors.append(jsonResponse["results"][0]["formatted_address"])
            print(jsonResponse["results"][0]["formatted_address"])

        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except Exception as err:
            print(f'Other error occurred: {err}')
        return render_template('maps.html', title='Google Maps API', form=form, posts=coors)
    return render_template('maps.html', title='Google Maps API', form=form)

if __name__ == '__main__':
    app.run(debug=True)