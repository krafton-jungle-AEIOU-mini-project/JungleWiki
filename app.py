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

   
if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)