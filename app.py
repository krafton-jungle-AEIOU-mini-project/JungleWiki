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

@app.route('/api/<id>/comment/create', methods =['POST'])
def post_comment(id):
    comment = request.form['comment']
    now = int(time.time())
    nickname = request.form['nickname']
    memo = {'postid': id, 'comment': comment ,'nickname' : nickname, 'date':now}
    db.comment.insert_one(memo)
    return jsonify({'code':1})
    #memo['_id'] = str(result.inserted_id)

   
if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)