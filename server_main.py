from functions import send_message_talkroom_users
from flask import Flask, request, jsonify
import json
import sqlite3
import uuid
import time

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
    talkroom_id = req_json['talkroom_id']
    sender_id = req_json['sender_id']
    message = req_json['message']
    timestamp = req_json['timestamp']

    # トークルーム参加者にメッセージを送信
    send_message_talkroom_users(talkroom_id, sender_id, message, timestamp)

    return "Success"


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


@app.route("/get_user_data", methods=["POST"])
def get_user_data():
    # 送信されたJsonから情報取り出し
    req_json = json.loads(request.data.decode('utf-8'))
    user_ids = req_json["user_ids"]

    # ユーザ情報を入れる変数
    user_data = {}

    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()

    # DBへ接続してユーザ情報取り出し
    for user_id in user_ids:
        user_info = cur.execute("""SELECT * FROM user WHERE user_id=?""",
                                (user_id, )).fetchone()

        # ユーザ情報を格納する
        user_data[user_id] = {
            "user_id": user_id,
            "name": user_info[2],
            "icon_url": user_info[3],
            "header_image_url": user_info[4]
        }

    cur.close()
    connect_db.close()

    # Jsonを返す
    return jsonify(user_data)


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


@app.route("/join_talkroom", methods=["POST"])
def join_talkroom():
    # 送信されたJsonから情報取り出し
    req_json = json.loads(request.data.decode('utf-8'))
    talkroom_id = req_json["talkroom_id"]
    user_ids = req_json["user_ids"]

    # ユーザidのリストをDB登録用に一文化
    user_ids_str = ""
    for user_id in user_ids:
        if user_id != "":
            user_ids_str += user_id + ";"

    # DBに接続 -> 現在の値取得
    connect_db = sqlite3.connect('talkroom.db')
    cur = connect_db.cursor()
    now_user_list = cur.execute("""SELECT user_list FROM talkroom WHERE id=?""",
                                (talkroom_id, )).fetchone()[0]

    # 更新
    cur.execute("""UPDATE talkroom SET user_list=? WHERE id=?""",
                (now_user_list+user_ids_str, talkroom_id))
    connect_db.commit()

    cur.close()
    connect_db.close()

    # ユーザ入室情報を知らせる
    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    user_name = ""
    for user_id in user_ids:
        user_name += cur.execute("""SELECT name FROM user WHERE user_id=?""",
                                (user_id, )).fetchone()[0] + " さん "
    send_message_talkroom_users(talkroom_id, "owner", user_name+"が入室しました", int(time.time()))

    cur.close()
    connect_db.close()

    return "Success"


@app.route("/exit_talkroom", methods=["POST"])
def exit_talkroom():
    # 送信されたJsonから情報取り出し
    req_json = json.loads(request.data.decode('utf-8'))
    talkroom_id = req_json["talkroom_id"]
    user_id = req_json["user_id"]

    # DBに接続 -> 現在の値取得
    connect_db = sqlite3.connect('talkroom.db')
    cur = connect_db.cursor()
    now_user_list = cur.execute("""SELECT user_list FROM talkroom WHERE id=?""",
                                (talkroom_id, )).fetchone()[0]

    # 更新
    now_user_list = now_user_list.replace(user_id+";", "")
    cur.execute("""UPDATE talkroom SET user_list=? WHERE id=?""",
                (now_user_list, talkroom_id))
    connect_db.commit()

    # もしこのユーザの退出で参加人数が0人になった場合はトークルームを削除
    if now_user_list == "":
        cur.execute("""DELETE FROM talkroom WHERE id=?""",
                    (talkroom_id,))
        connect_db.commit()

        cur.close()
        connect_db.close()

        return "Success"

    cur.close()
    connect_db.close()

    # ユーザ退室情報を知らせる
    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    user_name = cur.execute("""SELECT name FROM user WHERE user_id=?""",
                            (user_id,)).fetchone()[0] + " さん "
    send_message_talkroom_users(talkroom_id, "owner", user_name + "が退室しました", int(time.time()))

    cur.close()
    connect_db.close()

    return "Success"



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

    friends_list = [friend for friend in friends_list_db.split(";")][:-1]

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
    now_friends_list = [friend for friend in now_friends.split(";")]

    user_existence_count = cur.execute("""SELECT * FROM user WHERE user_id=?""",
                                 (add_friends_user_id, )).fetchall()

    # 現在の友達リストに追加するユーザが存在しないか，追加するユーザが登録済みのユーザかどうか判定
    if (add_friends_user_id not in now_friends_list) and (len(user_existence_count) == 1):
        now_friends += add_friends_user_id + ";"

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
                "user_list": [user for user in row[2].split(";")],
                "icon_url": row[3]
            }
        )

    cur.close()
    connect_db.close()

    # Jsonで返す
    return jsonify({"talkrooms": join_talkrooms})


@app.route("/get_talkroom_data", methods=["POST"])
def get_talkroom_data():
    # 送信されたJsonから情報を取り出す
    req_json = json.loads(request.data.decode('utf-8'))
    talkroom_id = req_json["talkroom_id"]

    # DB接続して指定IDのトークルーム情報を取り出す
    connect_db = sqlite3.connect('talkroom.db')
    cur = connect_db.cursor()
    talkroom_data = cur.execute("""SELECT * FROM talkroom WHERE id=?""",
                                (talkroom_id, )).fetchone()

    ret_dict = {
        "talkroom_id": talkroom_id,
        "talkroom_name": talkroom_data[1],
        "talkroom_user_list": [user for user in talkroom_data[2].split(";")],
        "talkroom_icon_url": talkroom_data[3]
    }

    cur.close()
    connect_db.close()

    # Jsonを返す
    return jsonify(ret_dict)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=1204)
