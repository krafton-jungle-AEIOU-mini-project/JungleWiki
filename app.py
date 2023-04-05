from pymongo import MongoClient
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import hashlib
import datetime
import jwt
import time
from pytz import timezone
from chatgpt import *
import bson
import threading
from tqdm import tqdm

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
            return redirect(url_for("redirectPage", alert="로그인 시간이 만료되었습니다. 다시 로그인 해주세요."))
        except jwt.exceptions.DecodeError:
            session.pop('Authorization', None)
            return redirect(url_for("redirectPage", alert="로그인 정보가 존재하지 않아 로그아웃 되었습니다."))
    else:
        return render_template('index.html')


@app.route('/join')
def join():
    if 'Authorization' in session:
        return redirect(url_for("home"))
    return render_template('join.html')


@app.route('/login')
def login():
    if 'Authorization' in session:
        return redirect(url_for("home"))
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
def detail():
    if 'Authorization' in session:
        token_receive = session['Authorization']
        try:
            payload = jwt.decode(token_receive, SECRET_KEY,
                                 algorithms=['HS256'])
            user_info = db.user.find_one({"id": payload['id']})
            return render_template('detail.html', isLogin=True, nickname=user_info["nick"])
        except jwt.ExpiredSignatureError:
            session.pop('Authorization', None)
            return render_template('detail.html', isLogin=False, alert="로그인 시간이 만료되었습니다. 다시 로그인 해주세요.")
        except jwt.exceptions.DecodeError:
            session.pop('Authorization', None)
            return render_template('detail.html', isLogin=False, alert="로그인 정보가 존재하지 않아 로그아웃 되었습니다.")
    else:
        return render_template('detail.html')


@app.route('/logout')
def logout():
    session.pop('Authorization', None)
    return render_template('index.html')


@app.route('/api/ask/list/<id>' , methods = ['GET'])
def read_article(id):
    filter = {'_id':bson.ObjectId(id)}
    filter2 = {'postid':id}
    rs = list()
    docs = list(db.memos.find(filter))
    docs2 = list(db.comment.find(filter2))
    for memo in docs:
        item = {
            'title':memo['title'],
            'content':memo['content'],
            'nickname':memo['nickname'],
            'date':datetime.datetime.fromtimestamp(memo['date'])
        }
        rs.append(item)
    for memo2 in docs2:
        item2 = {
            'comment':memo2['comment'],
            'date' :datetime.datetime.fromtimestamp(memo2['date']),
            'nickname' : memo2['nickname']
        }
    rs.append(item2)
    return jsonify({'code':1, 'data':rs})

@app.route('/api/ask/list', methods=['GET'])
def show_articles():
    filter = {}
    project = {}
    rs = list()
    docs = list(db.memos.find(filter, project).sort('date', -1))
   # docs = list(db.memos.find().sort({'date', -1}))
    # 시간으로 리스트 정리하기
    for memo in docs:
        item = {
            'title':memo['title'],
            'content':memo['content'],
            'nickname':memo['nickname'],
            'date':datetime.datetime.fromtimestamp(memo['date'])
        }
        rs.append(item)
    return jsonify({'code': 1, 'data': rs})
# def emptyString(id):
#         filter = {'_id': bson.ObjectId(id)}
#         content = "ChatGPT 답변중..."
#         update = {'$set': {'content': content}}
#         db.memos.update_one(filter,update)
# def __init__(self):
#     t = threading.Thread(target=self.chatgpt_comment())
#     t.start
#     t.daemon = True
#     t1 = threading.Thread(target=self.emptyString())
#     t1.start

    


@app.route('/api/ask/create', methods=['POST'])
def post_article():
    title = request.form['title']
    nickname = request.form['nickname']
    now = int(time.time())
    memo = {'title': title, 'content': "", 'nickname': nickname, 'date': now}
    result = db.memos.insert_one(memo)
    memo['_id'] = str(result.inserted_id)
    chatgpt_comment(memo['_id'], title)
    return jsonify({'code': 1, 'data': memo})


@app.route('/api/<id>/comment/create', methods=['POST'])
def post_comment(id):
    comment = request.form['comment']
    now = int(time.time())
    nickname = request.form['nickname']
    memo = {'postid': id, 'comment': comment,
            'nickname': nickname, 'date': now}
    db.comment.insert_one(memo)
    return jsonify({'code': 1})
    # memo['_id'] = str(result.inserted_id)


@app.route('/api/ask/<id>/comment/list', methods=['GET'])
def show_comment(id):
    filter = {'postid': id}
    project = {}
    rs = list()
    # docs = list(db.memos.find ().sort( { 'date' : 1 } ))
    docs = list(db.comment.find(filter, project).sort('date', 1))
    for memo in docs:
        item = {
            'nickname': memo['nickname'],
            'comment': memo['comment'],
            # '_id': str(memo['_id']),
            'date': datetime.datetime.fromtimestamp(memo['date'])
        }
        rs.append(item)
    return jsonify({'code': 1, 'data': rs})


def chatgpt_comment(id, title):
    # user_content = request.form['title']
    messages = []
    messages.append({"role": "user", "content": title})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages)
    chatgpt_reply = completion.choices[0].message["content"].strip()
    db.memos.update_one({'_id': bson.ObjectId(id)}, {
                        "$set": {"content": chatgpt_reply}})


@app.route('/redirect')
def redirectPage():
    alert = request.args.get('alert')
    session.pop('Authorization', None)
    return render_template('redirect.html', alert=alert)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
