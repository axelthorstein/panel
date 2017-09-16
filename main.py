import logging
import requests
import mimetypes

from flask import Flask
from flask import render_template
import pyrebase

app = Flask(__name__)

def detect_image(file_path):
    watson = "https://gateway-a.watsonplatform.net/visual-recognition/api/v3/detect_faces?api_key=9b4cc1ac0342de1c531f65f8c2d4410c42b7357f&version=2016-05-20"

    try:
        with open(file_path, 'rb') as image:
            filename = image.name
            mime_type = mimetypes.guess_type(
            filename)[0] or 'application/octet-stream'
            files = {'images_file': (filename, image, mime_type)}
            r = requests.request(method="POST", url=watson, files=files)
            json = r.json()
            gender = json['images'][0]['faces'][0]['gender']['gender']
            age = (json['images'][0]['faces'][0]['age']['max'] + json['images'][0]['faces'][0]['age']['min']) / 2
            return (gender, age)
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
    firebase = initialize_firebase()
    json = detect_image("assets/prez.jpg")
    return render_template('index.html', json=json, firebase=firebase)


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
