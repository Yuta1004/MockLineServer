from pyfcm import FCMNotification
import os
from flask import Flask, request
import json
import sqlite3

app = Flask(__name__)
url = ""


@app.route(url+"/")
def home():
    return "Welcome to MockLineServer Home Page!!"


@app.route(url+"/send_message", methods=["POST"])
def receive_send_info_json():
    req_json = json.loads(request.data.decode('utf-8'))
    talkroom_id = req_json['id']
    send_user_token = req_json['send_user_token']
    message = req_json['message']
    timestamp = req_json['timestamp']

    connect_db = sqlite3.connect('talkroom.db')
    cur = connect_db.cursor()
    talkroom_user_list = cur.execute("""SELECT user_list FROM talkroom WHERE id=?""", (talkroom_id, ))
    talkroom_user_list = talkroom_user_list.fetchone()[0].split(",")
    talkroom_user_tokens = [user_token for user_token in talkroom_user_list]
    cur.close()
    connect_db.close()

    send_data_to_users(user_tokens=talkroom_user_tokens,
                       send_user_token=send_user_token,
                       talkroom_id=talkroom_id,
                       message=message,
                       timestamp=timestamp)

    return "Success"


def send_data_to_users(user_tokens, send_user_token, talkroom_id, message, timestamp):
    api_key = os.getenv("FIREBASE_API_KEY")
    firebase = FCMNotification(api_key=api_key)

    send_data = {
        "talkroom_id": talkroom_id,
        "send_user": send_user_token,
        "message": message,
        "timestamp": timestamp
    }

    firebase.notify_multiple_devices(registration_ids=user_tokens,
                                     data_message=send_data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1204)
