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


def chatgpt_comment(id,title): 
   # user_content = request.form['title']
   messages = []
   messages.append({"role": "user", "content": title})
   completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
   chatgpt_reply = completion.choices[0].message["content"].strip()
   db.memos.update_one({'_id': bson.ObjectId(id)},{"$set":{"content":chatgpt_reply}})
   
if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)