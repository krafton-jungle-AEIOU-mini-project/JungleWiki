from pymongo import MongoClient
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import hashlib
import datetime
import jwt

client = MongoClient('localhost', 27017)
db = client.dbjungle

app = Flask(__name__)
SECRET_KEY = 'CRAFTON_AEIOU_5TEAM'
app.secret_key = SECRET_KEY


@app.route('/')
def home():
    if 'Authorization' in session:
        token_receive = session['Authorization']
        try:
            payload = jwt.decode(token_receive, SECRET_KEY,
                                 algorithms=['HS256'])
            user_info = db.user.find_one({"id": payload['id']})
            return render_template('index.html', isLogin=True, nickname=user_info["nick"])
        except jwt.ExpiredSignatureError:
            session.pop('Authorization', None)
            return render_template('index.html', isLogin=False, alert="로그인 시간이 만료되었습니다. 다시 로그인 해주세요.")
        except jwt.exceptions.DecodeError:
            session.pop('Authorization', None)
            return render_template('index.html', isLogin=False, alert="로그인 정보가 존재하지 않아 로그아웃 되었습니다.")
    else:
        return render_template('index.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
