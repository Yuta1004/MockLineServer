from pyfcm import FCMNotification
from flask import Flask, request
import json

app = Flask(__name__)
url = ""


@app.route(url+"/")
def home():
    return "Welcome to MockLineServer Home Page!!"


@app.route(url+"/send_message", methods=["POST"])
def send_message():
    return "Success_testcommit"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1204)
