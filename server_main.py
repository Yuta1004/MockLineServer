from pyfcm import FCMNotification
import os
from flask import Flask, request, jsonify
import json
import sqlite3
import uuid

app = Flask(__name__)
url = ""


@app.route(url + "/")
def home():
    return "Welcome to MockLineServer Home Page!!"


@app.route("/check_server", methods=["GET"])
def check_server():
    return "Server OK"


@app.route(url + "/send_message", methods=["POST"])
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
    talkroom_user_list = cur.execute("""SELECT user_list FROM talkroom WHERE id=?""", (talkroom_id,))
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
    # 送信されたJsonから情報を取り出す
    req_json = json.loads(request.data.decode('utf-8'))
    name = req_json["name"]
    id = req_json["id"]

    # ユーザDBに接続 -> ユーザ追加
    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    cur.execute("""INSERT INTO user VALUES (?, ?, ?, ?, ?, ?)""",
                (id, "none", name, "none", "none", "none"))
    connect_db.commit()
    cur.close()
    connect_db.close()

    return "Success"


@app.route("/update_user", methods=["POST"])
def update_user():
    # 送信されたJsonから情報取り出し
    req_json = json.loads(request.data.decode('utf-8'))
    user_id = req_json["id"]

    # ユーザDBに接続してidをもとにユーザ情報を取り出す
    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    user_info = cur.execute("""SELECT * FROM user WHERE user_id=?""", (user_id,)).fetchone()

    # 送信されたJsonのデータが空なら旧データで補完する
    items = []
    for idx, key in enumerate(["notify_token", "name", "icon_url", "header_image_url"]):
        if (key not in req_json.keys()) or (req_json[key] == ""):
            items.append(user_info[idx + 1])
        else:
            items.append(req_json[key])

    # ユーザ情報上書き
    cur.execute("""UPDATE user SET user_id=?, notify_token=?, name=?, icon_url=?, header_image_url=? WHERE user_id=?""",
                (user_id, items[0], items[1], items[2], items[3], user_id))
    connect_db.commit()
    cur.close()
    connect_db.close()

    return "Success"


@app.route("/get_user_info", methods=["POST"])
def get_user_info():
    # 送信されたJsonから情報取り出し
    req_json = json.loads(request.data.decode('utf-8'))
    user_id = req_json["user_id"]

    # DBへ接続してユーザ情報取り出し
    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    user_info = cur.execute("""SELECT * FROM user WHERE user_id=?""",
                            (user_id, )).fetchone()

    cur.close()
    connect_db.close()

    # Jsonを返す
    return jsonify({
        "user_id": user_id,
        "name": user_info[2],
        "icon_url": user_info[3],
        "header_image_url": user_info[4]
    })


@app.route("/make_talkroom", methods=["POST"])
def make_talkroom():
    # 送られてきたJsonから情報を取り出す
    req_json = json.loads(request.data.decode('utf-8'))
    user_list = req_json["user_list"]
    talkroom_name = req_json["talkroom_name"]

    # 新規ID生成(UUID: Random)
    talkroom_id = str(uuid.uuid4())

    # DBに接続してトークルームを追加する
    conncect_db = sqlite3.connect('talkroom.db')
    cur = conncect_db.cursor()
    cur.execute("""INSERT INTO talkroom VALUES (?, ?, ?, ?)""",
                (talkroom_id, talkroom_name, user_list, ""))
    conncect_db.commit()
    cur.close()
    conncect_db.close()

    # 生成されたIDをJsonで返す
    return jsonify({"talkroom_id": talkroom_id})


@app.route("/update_talkroom_info", methods=["POST"])
def update_talkroom_info():
    # 送られてきたJsonから情報を取り出す
    req_json = json.loads(request.data.decode('utf-8'))
    talkroom_id = req_json["talkroom_id"]

    # idをもとにトークルーム情報を取り出す
    connect_db = sqlite3.connect('talkroom.db')
    cur = connect_db.cursor()
    talkroom_info = cur.execute("""SELECT * FROM talkroom WHERE id=?""",
                                (talkroom_id,)).fetchone()

    # Jsonに含まれていないデータを旧データて補完する
    talkroom_name = req_json["talkroom_name"] if "talkroom_name" in req_json.keys() else talkroom_info[1]
    talkroom_user_list = req_json["talkroom_user_list"] if "talkroom_user_list" in req_json.keys() else talkroom_info[2]
    talkroom_icon_url = req_json["talkroom_icon_url"] if "talkroom_icon_url" in req_json.keys() else talkroom_info[3]

    # トークルーム情報変更
    cur.execute("""UPDATE talkroom SET name=?, user_list=?, icon_url=? WHERE id=?""",
                (talkroom_name, talkroom_user_list, talkroom_icon_url, talkroom_id))
    connect_db.commit()

    cur.close()
    connect_db.close()

    return "Success"


@app.route("/get_friends_list", methods=["POST"])
def get_friends():
    # 送信されたJsonから情報を取り出す
    req_json = json.loads(request.data.decode('utf-8'))
    user_id = req_json["user_id"]

    # DBに接続して友達リストを取り出す
    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    friends_list_db = cur.execute("""SELECT friends_list FROM user WHERE user_id=?""",
                                  (user_id,)).fetchone()[0]

    friends_list = [friend for friend in friends_list_db.split(",")][:-1]

    cur.close()
    connect_db.close()

    # Jsonで返す
    return jsonify({"friends_list": friends_list})


@app.route("/add_friends", methods=["POST"])
def add_friends():
    # 送信されたJsonから情報を取り出す
    req_json = json.loads(request.data.decode('utf-8'))
    user_id = req_json["user_id"]
    add_friends_user_id = req_json["add_friends_user_id"]

    # 自分自身ならエラー
    if user_id == add_friends_user_id:
        return "Userid is same"

    # DBに接続して現在の友達リストを取り出す
    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    now_friends = cur.execute("""SELECT friends_list FROM user WHERE user_id=?""",
                              (user_id, )).fetchone()[0]
    now_friends_list = [friend for friend in now_friends.split(",")]

    user_existence_count = cur.execute("""SELECT * FROM user WHERE user_id=?""",
                                 (add_friends_user_id, )).fetchall()

    # 現在の友達リストに追加するユーザが存在しないか，追加するユーザが登録済みのユーザかどうか判定
    if (add_friends_user_id not in now_friends_list) and (len(user_existence_count) == 1):
        now_friends += add_friends_user_id + ","

        cur.execute("""UPDATE user SET friends_list=? WHERE user_id=?""",
                    (now_friends, user_id))
        connect_db.commit()

        ret_message = "Success"
    elif len(user_existence_count) != 1:  # 存在しないユーザだった場合
        ret_message = "No Existnce User"
    else:  # 既に友達のユーザだった場合
        ret_message = "Already Added User"

    cur.close()
    connect_db.close()

    return ret_message


@app.route("/get_join_talkrooms", methods=["POST"])
def get_join_talkrooms():
    # 送信されたJsonから情報を取り出す
    req_json = json.loads(request.data.decode('utf-8'))
    user_id = req_json["id"]

    # トークルームDBに接続してidをもとに参加トークルームを取り出す
    connect_db = sqlite3.connect('talkroom.db')
    cur = connect_db.cursor()
    talkrooms = cur.execute("""SELECT * FROM talkroom WHERE user_list LIKE ?""",
                            ("%" + user_id + "%",)).fetchall()

    # DBから取り出した情報をリストに入れていく
    join_talkrooms = []
    for row in talkrooms:
        join_talkrooms.append(
            {
                "id": row[0],
                "name": row[1],
                "user_list": [user for user in row[2].split(",")],
                "icon_url": row[3]
            }
        )

    cur.close()
    connect_db.close()

    # Jsonで返す
    return jsonify({"talkrooms": join_talkrooms})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1204)
