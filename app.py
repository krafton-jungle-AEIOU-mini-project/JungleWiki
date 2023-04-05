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


@app.route('/join')
def join():
    if 'Authorization' in session:
        token_receive = session['Authorization']
        try:
            payload = jwt.decode(token_receive, SECRET_KEY,
                                 algorithms=['HS256'])
            user_info = db.user.find_one({"id": payload['id']})
            return redirect(url_for("home", alert="이미 로그인 된 상태라 홈으로 이동합니다.", isLogin=True, nickname=user_info["nick"]))
        except jwt.ExpiredSignatureError:
            session.pop('Authorization', None)
        except jwt.exceptions.DecodeError:
            session.pop('Authorization', None)
    return render_template('join.html')


@app.route('/login')
def login():
    if 'Authorization' in session:
        token_receive = session['Authorization']
        try:
            payload = jwt.decode(token_receive, SECRET_KEY,
                                 algorithms=['HS256'])
            user_info = db.user.find_one({"id": payload['id']})
            return redirect(url_for("home", alert="이미 로그인 된 상태라 홈으로 이동합니다.", isLogin=True, nickname=user_info["nick"]))
        except jwt.ExpiredSignatureError:
            session.pop('Authorization', None)
        except jwt.exceptions.DecodeError:
            session.pop('Authorization', None)
    return render_template('login.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    if result is not None:
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        session['Authorization'] = token
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'fail', 'errorField': 'userId', 'msg': '아이디(로그인 전용 아이디) 또는 비밀번호를 잘못 입력했습니다.<br/> 입력하신 내용을 다시 확인해주세요.'})


@app.route('/api/join', methods=['POST'])
def api_join():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']

    if (db.user.find_one({'id': id_receive}) is not None):
        return jsonify({'result': 'fail', 'errorField': 'userId', 'msg': '이미 존재하는 아이디 입니다.'})
    elif (db.user.find_one({'nick': nickname_receive})):
        return jsonify({'result': 'fail', 'errorField': 'userNickname', 'msg': '이미 존재하는 닉네임 입니다.'})

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.user.insert_one(
        {'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive})

    return jsonify({'result': 'success'})


@app.route('/detail')
def detailPage():
    return render_template('detail.html')


@app.route('/logout')
def logout():
    session.pop('Authorization', None)
    return render_template('index.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
