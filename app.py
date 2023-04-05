from flask import Flask, render_template
import time
from pytz import timezone
from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request
from datetime import datetime as dt,timezone, timedelta
from chatgpt import *
import bson
import json
app = Flask(__name__)
client = MongoClient('localhost', 27017)
db = client.dbjungle
@app.route('/')
def home():
   return render_template('index.html')
@app.route('/api/ask/list', methods=['GET'])
def show_articles():
    filter = {}
    project = {}
    rs = list()
    docs = list(db.memos.find(filter, project).sort('date', -1))
   # docs = list(db.memos.find().sort({'date', -1}))
    #시간으로 리스트 정리하기
    for memo in docs:
        item = {
            '_id': str(memo['_id']),
            'title': memo['title'],
            'content': memo['content'],
            'nickname': memo['nickname'],
            'date': dt.fromtimestamp(memo['date'])
        }
        rs.append(item)
    
    return jsonify({'code': 1, 'data': rs})
@app.route('/api/ask/create', methods=['POST'])
def post_article():
    
    title = request.form['title']
    nickname = request.form['nickname']
    now = int(time.time())
    memo = {'title': title, 'content':"로딩중입니다", 'nickname':nickname,'date':now}
    result = db.memos.insert_one(memo)
    memo['_id'] = str(result.inserted_id)
    chatgpt_comment(memo['_id'],title)
    return jsonify({'code': 1, 'data': memo})

@app.route('/api/<id>/comment/create', methods =['POST'])
def post_comment(id):
    comment = request.form['comment']
    now = int(time.time())
    nickname = request.form['nickname']
    memo = {'postid': id, 'comment': comment ,'nickname' : nickname, 'date':now}
    db.comment.insert_one(memo)
    return jsonify({'code':1})
    #memo['_id'] = str(result.inserted_id)
@app.route('/api/ask/<id>/comment/list' , methods = ['GET'] )
def show_comment(id):
   filter = {'postid':id}
   project = {}
   rs = list()
   #docs = list(db.memos.find ().sort( { 'date' : 1 } ))
   docs = list(db.comment.find(filter, project).sort('date', 1))
   for memo in docs:
       item = {
           'nickname':memo['nickname'],
           'comment':memo['comment'],
           #'_id': str(memo['_id']),
           'date': dt.fromtimestamp(memo['date'])
       }
       rs.append(item)
   return jsonify({'code':1,'data':rs})

def chatgpt_comment(id,title): 
   # user_content = request.form['title']
   messages = []
   messages.append({"role": "user", "content": title})
   completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
   chatgpt_reply = completion.choices[0].message["content"].strip()
   db.memos.update_one({'_id': bson.ObjectId(id)},{"$set":{"content":chatgpt_reply}})
   
if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)