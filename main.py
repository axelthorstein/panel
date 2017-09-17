import logging

from flask import Flask, render_template
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db as database
from firebase_admin import storage
from oauth2client.service_account import ServiceAccountCredentials

from watson_developer_cloud import VisualRecognitionV3
from gifextract import get_frame


app = Flask(__name__)


global admin
admin = firebase_admin.initialize_app(
    credentials.Certificate('firebase_credentials.json'),
    name='panel-180102',
    options={"databaseURL": "https://panel-180102.firebaseio.com/"})


def detect_image(file_path):
    visual_recognition = VisualRecognitionV3('2016-05-20', api_key='9b4cc1ac0342de1c531f65f8c2d4410c42b7357f')
    image_data = visual_recognition.detect_faces(images_url=file_path)

    return [face for face in image_data['images'][0]['faces']]


@app.route('/grid')
def grid():
    return render_template('grid.html')

@app.route('/data')
def data():
    return render_template('data.html')


def get_image_url(id):
    image_url = "https://firebasestorage.googleapis.com/v0/b/panel-180102.appspot.com/o/images%2f" \
        + id \
        + ".png?alt=media&token="
    scopes = ['https://www.googleapis.com/auth/firebase.database',
              'https://www.googleapis.com/auth/userinfo.email',
              "https://www.googleapis.com/auth/cloud-platform"]

    credentials = ServiceAccountCredentials.from_json_keyfile_name('firebase_credentials.json', scopes)

    return detect_image(image_url + credentials.get_access_token().access_token)


def update_gender_aggregate(image_data, id, face):
    gender_agg = database.reference("data/gender_agg", app=admin).get()
    database.reference("images/" + id, app=admin).set(image_data)

    if face['gender']['score'] > 0.15:
        if not gender_agg:
            gender_agg = {"MALE": 0, "FEMALE": 0}
        if face['gender']['gender'] == "MALE":
            gender_agg["MALE"] += 1
        else:
            gender_agg["FEMALE"] += 1
        database.reference("data/gender_agg", app=admin).update(gender_agg)


def update_age_aggregate(image_data, id, face):
    age_agg = database.reference("data/age_agg", app=admin).get()
    if not age_agg:
        age_agg = {"avg_age": 20, "num_ages": 1}
    age_agg['avg_age'] = ((age_agg['avg_age'] * age_agg['num_ages'])
                          + ((face["age"]["max"]
                              + face["age"]["min"]) / 2)) / (age_agg['num_ages'] + 1)
    age_agg['num_ages'] += 1

    database.reference("data/age_agg", app=admin).update(age_agg)


def update_aggregates(image_data, id):
    for face in image_data:
        update_gender_aggregate(image_data, id, face)
        update_age_aggregate(image_data, id, face)


@app.route('/images/<id>', methods=["GET"])
def images(id):
    filename = id + ".gif"
    bucket = storage.bucket(name="panel-180102.appspot.com", app=admin)

    # Download the gif locally
    bucket.blob("gifs/" + filename).download_to_filename("assets/" + filename)

    # Extract the middle frame from the gif
    get_frame("assets/" + filename, id, database, bucket)

    # Extract age and gender from the frame with IBM's Watson Image Recognition API
    image_data = get_image_url(id)

    # Update the gender and age aggregates
    update_aggregates(image_data, id)

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
