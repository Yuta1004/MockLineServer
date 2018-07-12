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
    # 送信されたJSONから各種情報読み取り
    req_json = json.loads(request.data.decode('utf-8'))
    talkroom_id = req_json['id']
    send_user_token = req_json['send_user_token']
    message = req_json['message']
    timestamp = req_json['timestamp']

    # 該当トークルームに参加しているユーザを取得
    connect_db = sqlite3.connect('talkroom.db')
    cur = connect_db.cursor()
    talkroom_user_list = cur.execute("""SELECT user_list FROM talkroom WHERE id=?""", (talkroom_id, ))
    talkroom_user_list = talkroom_user_list.fetchone()[0].split(",")
    cur.close()
    connect_db.close()

    # ユーザIDをもとに，ユーザDBから通知トークンを取得
    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    users_token = []
    for user_id in talkroom_user_list:
        token = cur.execute("""SELECT notify_token FROM user WHERE user_id=?""",
                            (user_id,)).fetchone()[0]
        users_token.append(token)
    cur.close()
    connect_db.close()

    send_data_to_users(user_tokens=users_token,
                       send_user_token=send_user_token,
                       talkroom_id=talkroom_id,
                       message=message,
                       timestamp=timestamp)

    return "Success"


def send_data_to_users(user_tokens, send_user_token, talkroom_id, message, timestamp):
    api_key = os.getenv("FIREBASE_API_KEY")
    firebase = FCMNotification(api_key=api_key)

    # 送信データ
    send_data = {
        "talkroom_id": talkroom_id,
        "send_user": send_user_token,
        "message": message,
        "timestamp": timestamp
    }

    # ユーザへ送信
    firebase.notify_multiple_devices(registration_ids=user_tokens,
                                     data_message=send_data)


@app.route("/add_user", methods=["POST"])
def add_user():
    req_json = json.loads(request.data.decode('utf-8'))
    name = req_json["name"]
    id = req_json["id"]

    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    cur.execute("""INSERT INTO user VALUES (?, ?, ?, ?, ?)""",
                (id, "none", name, "none", "none"))
    connect_db.commit()
    cur.close()
    connect_db.close()

    return "Success"


@app.route("/update_user", methods=["POST"])
def update_user():
    req_json = json.loads(request.data.decode('utf-8'))
    user_id = req_json["id"]

    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    user_info = cur.execute("""SELECT * FROM user WHERE user_id=?""", (user_id, )).fetchone()

    notify_token = req_json["notify_token"] if "notify_token" in req_json.keys() else user_info[1]
    name = req_json["name"] if "name" in req_json.keys() else user_info[2]
    icon_url = req_json["icon_url"] if "icon_url" in req_json.keys() else user_info[3]
    header_image_url = req_json["header_image_url"] if "header_image_url" in req_json.keys() else user_info[4]

    cur.execute("""UPDATE user SET user_id=?, notify_token=?, name=?, icon_url=?, header_image_url=? WHERE user_id=?""",
                (user_id, notify_token, name, icon_url, header_image_url, user_id))
    connect_db.commit()
    cur.close()
    connect_db.close()

    return "Success"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1204)
