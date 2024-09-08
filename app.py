import os
from flask import Flask, request, abort,jsonify,render_template
from pymongo import MongoClient
import datetime
import logging
from sys import stderr
from bson import ObjectId
import json
from dotenv import load_dotenv


logging.basicConfig(stream=stderr)

app = Flask(__name__)
# Load environment variables from .env file
load_dotenv()
mongo_uri = os.getenv('MONGODB_URI')

# Create a new client and connect to the server
client = MongoClient(mongo_uri)
db = client['github_events']
collection = db['events']

@app.route('/')
def welcome():
    return "Welcome "

@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.headers.get('X-GitHub-Event')  # X-GitHub-Event specifies the type of event that occurred
    try:
        payload = request.json 
    except Exception:
        logging.warning('Request parsing failed')
        abort(400)
    message=""

    if event == 'push': #push
        author = payload['pusher']['name']
        to_branch = payload['ref'].split('/')[-1]
        timestamp = datetime.datetime.now()
        message = f"{author} pushed to {to_branch} on {timestamp.replace(microsecond=0).strftime('%d %B %Y - %I:%M %p UTC')}"
    
    elif event == "pull_request":
        action = payload['action']
        author = payload['pull_request']['user']['login']
        from_branch = payload['pull_request']['head']['ref']
        to_branch = payload['pull_request']['base']['ref']
        timestamp = datetime.datetime.now()
        
        if action == 'closed' and payload['pull_request']['merged']:  # merged
            message = f"{author} merged branch from {from_branch} to {to_branch} on {timestamp.replace(microsecond=0).strftime('%d %B %Y - %I:%M %p UTC')}"
        elif action in ['opened', 'closed']: #pull request
            message = f"{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp.replace(microsecond=0).strftime('%d %B %Y - %I:%M %p UTC')}"

    collection.insert_one({"event": event, 'message': message, 'timestamp': timestamp})
    return {'status': 'success'}, 200

@app.route('/api/get-latest-events', methods=['GET'])
def get_latest_events():
    # Fetch the latest 10 events from MongoDB
    events = collection.find().sort('timestamp', -1).limit(10)
    # Convert ObjectId to string for each event
    result = []
    for event in events:
        if '_id' in event:
            event['_id'] = str(event['_id'])
        result.append(event)

    return {'events': result}
@app.route('/api/print',methods=['GET'])
def print_events():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
