import requests
import json

req = {
    "id": 1234,
    "name": "test_user"
}
ret = requests.post("http://localhost:1204/send_message", json.dumps(req)).text
print(ret)
