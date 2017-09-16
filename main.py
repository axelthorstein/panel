import logging
import requests
import mimetypes

from flask import Flask
from flask import render_template
import pyrebase

from watson_developer_cloud import VisualRecognitionV3
from gifextract import get_frame


app = Flask(__name__)

def detect_image(file_path):
#    import json
    watson = "https://gateway-a.watsonplatform.net/visual-recognition/api/v3/detect_faces?api_key=9b4cc1ac0342de1c531f65f8c2d4410c42b7357f&version=2016-05-20"
#    visual_recognition = VisualRecognitionV3('2016-05-20', api_key='9b4cc1ac0342de1c531f65f8c2d4410c42b7357f')
#    image_data = visual_recognition.detect_faces(images_url=file_path)
#    print(image_data)
#    gender = image_data['images'][0]['faces'][0]['gender']['gender']
#    age = (image_data['images'][0]['faces'][0]['age']['max'], image_data['images'][0]['faces'][0]['age']['min'], image_data['images'][0]['faces'][0]['age']['score'])
#    return (gender, age)

    try:
        with open(file_path, 'rb') as image:
            filename = image.name
            mime_type = mimetypes.guess_type(
            filename)[0] or 'application/octet-stream'
            files = {'images_file': (filename, image, mime_type)}
            json = requests.request(method="POST", url=watson, files=files).json()
            return json['images'][0]['faces'][0]
    except:
        print("An Error occured uploading files")


def initialize_firebase():
    config = {
        "apiKey": "AIzaSyDTYAGexqXARKksJyCyVmfqpQvDWf7wbJ0",
        "authDomain": "panel-180102.firebaseapp.com",
        "databaseURL": "https://panel-180102.firebaseio.com",
        "storageBucket": "https://panel-180102.appspot.com/"
    }

    return  pyrebase.initialize_app(config)


@app.route('/')
def addtopanel():
    return "Home"


@app.route('/images/<id>', methods=["GET"])
def images(id):
    firebase = initialize_firebase()
    firebase.auth()
    database = firebase.database()
    storage = firebase.storage()

    gif_data = storage.child("images/" + id + ".gif")
    print(storage.credentials)
    gif = storage.child("images/").child(id + ".gif").get_url(None)
    print(gif)
    get_frame(gif, id, database)
    image_url = database.child("images").child(id).child('image').get_url()
    image_data = detect_image(image_url)
    firebase.child("images").child(id).set(image_data)
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
