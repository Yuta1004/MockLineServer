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
    req_json = json.loads(request.data.decode('utf-8'))
    talkroom_id = req_json['id']
    send_user_id = req_json['send_user_id']
    message = req_json['message']

    return "Success"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1204)
