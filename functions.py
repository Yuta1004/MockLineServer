import sqlite3
import os
from pyfcm import FCMNotification


def send_message_talkroom_users(talkroom_id, sender_id, message, timestamp):
    # 該当トークルームに参加しているユーザとトークルーム名を取得
    connect_db = sqlite3.connect('talkroom.db')
    cur = connect_db.cursor()
    talkroom_data = cur.execute("""SELECT * FROM talkroom WHERE id=?""", (talkroom_id,)).fetchone()
    talkroom_name = talkroom_data[1]
    cur.close()
    connect_db.close()

    # 送信ユーザを除外
    talkroom_user_list = talkroom_data[2].replace(sender_id + ";", "").split(";")

    # ユーザIDをもとに，ユーザDBから通知トークンを取得
    connect_db = sqlite3.connect('user.db')
    cur = connect_db.cursor()
    user_tokens = []
    for user_id in talkroom_user_list:
        if user_id == "":
            continue

        token = cur.execute("""SELECT notify_token FROM user WHERE user_id=?""",
                            (user_id,)).fetchone()[0]
        user_tokens.append(token)
    cur.close()
    connect_db.close()

    # Firebaseを通してPush通信
    api_key = os.getenv("FIREBASE_API_KEY")
    firebase = FCMNotification(api_key=api_key)

    # 送信データ
    send_data = {
        "talkroom_id": talkroom_id,
        "talkroom_name": talkroom_name,
        "sender_id": sender_id,
        "message": message,
        "timestamp": timestamp
    }

    # ユーザへ送信
    firebase.notify_multiple_devices(registration_ids=user_tokens,
                                     data_message=send_data)
