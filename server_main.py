from pyfcm import FCMNotification
from flask import Flask, request
import json
import sqlite3

app = Flask(__name__)
url = ""


@app.route(url+"/")
def home():
    return "Welcome to MockLineServer Home Page!!"


@app.route(url+"/send_message", methods=["POST"])
def send_message():
    req_json = json.loads(request.data.decode('utf-8'))
    talkroom_id = req_json['id']
    send_user_token = req_json['send_user_token']
    message = req_json['message']

    connect_db = sqlite3.connect('talkroom.db')
    cur = connect_db.cursor()
    talkroom_user_list = cur.execute("""SELECT user_list FROM talkroom WHERE id=?""", (talkroom_id, ))
    talkroom_user_list = talkroom_user_list.fetchone()[0].split(",")
    talkroom_user_tokens = [user_token for user_token in talkroom_user_list]
    cur.close()
    connect_db.close()

    return "Success"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1204)
