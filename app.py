from datetime import datetime
import random
import cohere
from icecream import ic
import json
import time
import os
from flask import Flask, redirect, render_template,app,request,session,jsonify
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
import uuid

import pytz

load_dotenv()


client = MongoClient(os.getenv("mongodb"))
db = client['flashcards']
devices_collection = db['devices']

co = cohere.ClientV2(api_key="ZIQIaTaVvw42UxMCPKnKzK19lcyxlk0Z0zRewScU")
exec_time = ""
with open("app.json","r") as f:
    json_data = json.load(f)
    system_messages = json_data[0]
    random_facts = json_data[1]
    






app = Flask(__name__)
app.secret_key = os.getenv("appKey")


def generate_id():
    """Generate a simple UUID."""
    return str(uuid.uuid4())

def time_now():
    saudi_tz = pytz.timezone('Asia/Riyadh')
    current_time = datetime.now(saudi_tz).strftime("%A, %dth of %B, %I:%M %p")
    ic(current_time)
    return current_time


def increment_times_generated():
   
    device_id = session.get("_id")
    if device_id:
        device_id = ObjectId(device_id)

        times_generated_user = devices_collection.find_one({"_id":device_id})['device']['times_generated']
        total_flashcards_generated_user = devices_collection.find_one({"_id":device_id})['device']['total_flashcards_generated']
        total_flashcards_generated_user += int(number_of_flashcards)

        devices_collection.update_one({"_id":device_id},{"$set":{"device.times_generated":times_generated_user,"device.total_flashcards_generated":total_flashcards_generated_user}})
    
   



def make_flashcards(text,difficulty,number_of_flashcards):
    """
    Generate flashcards from a given text, using the Command-R AI model.

    Parameters
    ----------
    text : str
        The text to generate flashcards from.
    difficulty : int, 
        The difficulty level of the flashcards, ranging from 1 to 5.
    number_of_flashcards : int, default=number_of_flashcards
        The number of flashcards to generate.

    Returns
    -------
    flashcards : list
        A list of dictionaries, each containing a 'question' and an 'answer'.
    """
    start_time = time.time()
    difficulty-=1 # for user input and list indexing
    ic(difficulty,len(system_messages))
    print(f"generating {number_of_flashcards} flashcards with difficulty level {difficulty}...")
    
    try:
        res = co.chat(
        model="command-r-plus-08-2024",
        messages=[
            {
                "role": "user",
                "content": f"Generate {number_of_flashcards} flashcards from the following text: {text}",
            },
            {
                "role": "system",
                "content":system_messages[difficulty].replace("flashcard.number", str(number_of_flashcards)),
            }
        ],
    )   
       

        flashcards = json.loads(res.message.content[0].text)
        end_time = time.time()
        global exec_time
        exec_time = round(end_time - start_time,2)
     
        print(f"Successfully generated flashcards, in {exec_time} seconds!")
        return flashcards
    except Exception as e:
        print(e)
        return []








@app.route("/", methods=["GET", "POST"])
def home():
    theme = session.get("theme")
    random_fact = random.choice(random_facts)
    device_id = session.get("_id")
    if device_id:
        device_id = ObjectId(device_id)
        device = devices_collection.find_one({"_id":device_id})
        if not device:
            session.clear()
            return redirect("/")
   

    if request.method == "POST":
        text = request.form.get("input")
        global difficulty
        global number_of_flashcards #so i can use it in the flashcards page
        global flashcards

        difficulty = request.form.get("difficulty")
        number_of_flashcards = request.form.get("number_of_flashcards")
        flashcards = make_flashcards(text,difficulty = int(difficulty),number_of_flashcards = int(number_of_flashcards))

        device_id = session.get("_id")
        print(device_id)
        try:
            update = devices_collection.update_one({"_id": ObjectId(device_id)}, {"$push": {"device.flashcards": flashcards}})
            ic(update)
        except Exception as e:
            print(f"Error updating device flashcards: {e}")
            return redirect("/")

        for flashcard in flashcards:
            flashcard["id"] = generate_id()
    
        increment_times_generated()
        return redirect("/flashcards")
    return render_template("home.html",theme = theme,random_fact = random_fact) if theme else render_template("home.html",random_fact = random_fact)




@app.route("/flashcards",methods=["GET", "POST"])
def flashcards():
    theme = session.get("theme")
    if not exec_time:
        return redirect("/")
  
    return render_template("flashcards.html",flashcards = flashcards,exec_time = exec_time,theme = theme,difficulty = difficulty,number_of_flashcards = number_of_flashcards) if theme else render_template("flashcards.html",flashcards = flashcards,exec_time = exec_time,difficulty = difficulty,number_of_flashcards = number_of_flashcards)


@app.route("/theme",methods=["POST"])
def theme():
    request_data = str(request.data)
    ic(request_data)
    theme = request_data.replace("'","").strip('b')
    ic(theme)
    session["theme"] = theme
    print(f"set the new theme to {session['theme']}.")
    return "success"



@app.route('/collect_device_info', methods=['POST'])
def collect_device_info():
    data = request.get_json()
    headers = dict(request.headers)
    ic("DEVICE INFO RECIEVED")
    # Extract and print each data point
    screen_res = data.get('screen_resolution')
    browser = data.get('browser')
    platform = data.get('platform')
    cpu_cores = data.get('cpu_cores')
    memory = data.get('memory')
    time_zone = data.get('timezone')
    user_ip = headers['X-Forwarded-For'] if headers['Host'] == "snappycards.up.railway.app" else request.remote_addr
    
    devices = list(devices_collection.find({}))
    ic(list(devices))
   
   

    device_query = {
        "device.screen_res": screen_res,
        "device.browser": browser,
        "device.platform": platform,
        "device.cpu_cores": cpu_cores,
        "device.memory": memory,
        "device.user_ip": user_ip
    }

    existing_device = devices_collection.find_one(device_query)

    if existing_device:
        devices_collection.update_one(device_query,{"$inc":{"device.times_visited":1}})
        devices_collection.update_one(device_query,{"$set":{"device.last_time_visited":time_now()}})
    else: 
        device = {
        "flashcards":[],
        "screen_res":screen_res,
        "browser":browser,
        "platform":platform,
        "cpu_cores":cpu_cores,
        "memory":memory,
        "user_ip":user_ip,
        "times_visited":1,
        "first_time_visited":time_now(),
        "last_time_visited":time_now(),
        "time_zone":time_zone,
        "times_generated":0,
        "total_flashcards_generated":0

    }
        
        devices_collection.insert_one({"device":device})
        existing_device = devices_collection.find_one(device_query)

   
    try:
        session['_id'] = str(existing_device['_id'])
        return redirect("/")
    except Exception as e:
        print(f"Error found: {e}")
        ic( f"{existing_device}")
    
    
    ic("DEVICE INFO SAVED SUCCESSFULLY")
 
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(debug=True,port=8080,host="0.0.0.0")








