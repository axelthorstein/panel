import logging
import requests
import mimetypes

from flask import Flask, render_template, url_for
import pyrebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db as database
from firebase_admin import storage
from firebase_admin import auth
from oauth2client.service_account import ServiceAccountCredentials

from watson_developer_cloud import VisualRecognitionV3
from gifextract import get_frame


app = Flask(__name__)

global admin
admin = firebase_admin.initialize_app(credentials.Certificate('firebase_credentials.json'), name='panel-180102', options={"databaseURL": "https://panel-180102.firebaseio.com/"})


def detect_image(file_path):
    import json
    watson = "https://gateway-a.watsonplatform.net/visual-recognition/api/v3/detect_faces?api_key=9b4cc1ac0342de1c531f65f8c2d4410c42b7357f&version=2016-05-20"
    visual_recognition = VisualRecognitionV3('2016-05-20', api_key='9b4cc1ac0342de1c531f65f8c2d4410c42b7357f')
    image_data = visual_recognition.detect_faces(images_url=file_path)
    data = []
    for face in image_data['images'][0]['faces']:
        data.append(face)

    return data

def initialize_firebase():
    cred = credentials.Certificate('firebase_credentials.json')
    admin = firebase_admin.initialize_app(cred, name='panel-180102', options={"databaseURL": "https://panel-180102.firebaseio.com/"})

    return admin

def get_admin():
    if not firebase_admin:
        return initialize_firebase()
    return firebase_admin.get_app()


@app.route('/grid')
def grid():
    return render_template('grid.html')


@app.route('/images/<id>', methods=["GET"])
def images(id):
    bucket = storage.bucket(name="panel-180102.appspot.com", app=admin)

    gender_agg = database.reference("data/gender_agg", app=admin).get()

    age_agg = database.reference("data/age_agg", app=admin).get()

    filename = id + ".gif"

    blob = bucket.blob("gifs/" + filename)
    blob.download_to_filename("assets/" + filename)

    get_frame("assets/" + filename, id, database, bucket)

    #image_url = bucket.blob("images/" + id + ".png").generate_signed_url(100, method="GET", )
    image_url = "https://firebasestorage.googleapis.com/v0/b/panel-180102.appspot.com/o/images%2f" + id + ".png?alt=media&token="
    scopes = [
                        'https://www.googleapis.com/auth/firebase.database',
                        'https://www.googleapis.com/auth/userinfo.email',
                        "https://www.googleapis.com/auth/cloud-platform"
                    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name('firebase_credentials.json', scopes)

    image_data = detect_image(image_url + credentials.get_access_token().access_token)
    for face in image_data:
        database.reference("images/" + id, app=admin).set(image_data)
        if face['gender']['score'] > 0.26:
            if not gender_agg:
                gender_agg = {"MALE": 0, "FEMALE": 0}
            if face['gender']['gender'] == "MALE":
                gender_agg["MALE"] += 1
            else:
                print(image_data)
                gender_agg["FEMALE"] += 1
            database.reference("data/gender_agg", app=admin).update(gender_agg)

        if not age_agg:
            age_agg = {"avg_age": 20, "num_ages": 1}
        age_agg['avg_age'] = ((age_agg['avg_age'] * age_agg['num_ages']) + ((face["age"]["max"] + face["age"]["min"]) / 2)) / (age_agg['num_ages'] + 1)
        age_agg['num_ages'] += 1

        database.reference("data/age_agg", app=admin).update(age_agg)

    return id


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
# This is used when running locally. Gunicorn is used to run the
# application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
