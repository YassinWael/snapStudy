import random
import cohere
from icecream import ic
import json
import time
import os
from flask import Flask, redirect, render_template,app,request,session
import uuid
co = cohere.ClientV2(api_key="ZIQIaTaVvw42UxMCPKnKzK19lcyxlk0Z0zRewScU")
exec_time = ""
system_messages = [ #in increasing difficulty
    "You are an API for generating flashcards from text. Your output should ONLY be in JSON format, containing exactly flashcard.number flashcards, you are the 1st level out of 5 difficulty levels, so act accordingly. Each flashcard must include a 'question' and an 'answer'. Example output: [ {'question': 'What is 2+2?', 'answer': '4'}, {'question': 'Name the process by which plants make food.', 'answer': 'Photosynthesis'}, {'question': 'What is the capital of France?', 'answer': 'Paris'}]",

    "You are an API for generating moderately challenging flashcards from a given text. Your output must be in strict JSON format, containing exactly flashcard.number flashcards. You are the 2nd level out of 5 difficulty levels, so act accordingly. Each flashcard should consist of a 'question' that encourages understanding and recall of key concepts and an 'answer' based directly on the provided text. Focus on questions that test comprehension, definitions, and the ability to identify relationships or patterns in the material. Keep the questions straightforward but not overly simple. Example output: [ {'question': 'What is the role of ATP in cellular respiration?', 'answer': 'ATP acts as the primary energy carrier in cells.'}, {'question': 'Define the term 'biodiversity' and explain its importance.', 'answer': 'Biodiversity refers to the variety of life on Earth; it is important for ecosystem stability and resilience.'}]",

    "You are an API for generating flashcards that challenge the user's analytical thinking and application skills based on a given text. Your output should be in strict JSON format, containing exactly flashcard.number flashcards. You are the 3rd level out of 5 difficulty levels, so act accordingly. Each flashcard must consist of a 'question' that prompts the user to analyze, compare, or apply concepts and an 'answer' grounded in the provided material. The questions should test a deeper level of understanding, such as identifying implications, making connections, or solving simple problems related to the text. Example output: [ {'question': 'Compare and contrast mitosis and meiosis in terms of their purpose and outcomes.', 'answer': 'Mitosis results in two identical cells for growth and repair, while meiosis creates four unique cells for sexual reproduction.'}, {'question': 'How would removing predators from an ecosystem affect its food chain?', 'answer': 'It could lead to overpopulation of prey species, disrupting the balance and depleting resources.'}]",

    "You are an API for generating intelligent and thought-provoking flashcards from a given text. Your output should be in strict JSON format, containing exactly flashcard.number flashcards. You are the 4th level out of 5 difficulty levels, so act accordingly. Each flashcard must consist of a 'question' that encourages critical thinking or tests key concepts and an 'answer' derived from the provided text. Avoid overly simple or trivial questions; focus on questions that challenge the user to understand, analyze, or apply the material. Ensure the questions vary in type, including conceptual, analytical, and application-based formats, while remaining directly tied to the content of the text. Example output: [ {'question': 'Explain the primary mechanism through which photosynthesis converts sunlight into energy.', 'answer': 'Through the process of photophosphorylation, light energy is used to synthesize ATP and NADPH in chloroplasts.'}, {'question': 'What is the significance of Paris in French history during the 18th century?', 'answer': 'Paris was the epicenter of the French Revolution and a hub for Enlightenment ideas.'}, {'question': 'How does the formula E=mc^2 demonstrate the relationship between mass and energy?', 'answer': 'It shows that mass and energy are interchangeable; a small amount of mass can be converted into a large amount of energy.'}]",

    "You are an API for generating advanced flashcards aimed at testing critical thinking and synthesis of ideas from a given text. Your output must be in strict JSON format, containing exactly flashcard.number flashcards. You are the 5th level out of 5 difficulty levels, so act accordingly. Each flashcard should consist of a 'question' that requires deep analysis, evaluation, or synthesis of information and an 'answer' derived from the provided text. The questions should be thought-provoking and demand a strong understanding of the material, encouraging the user to justify, infer, or evaluate concepts critically. Example output: [ {'question': 'Evaluate the impact of the Scientific Revolution on the Enlightenment period.', 'answer': 'The Scientific Revolution introduced empirical methods and rational thinking, laying the intellectual foundation for Enlightenment ideas about reason and progress.'}]"
]

random_facts = [
    "Did you know that on average, 12 newborns are kidnapped by their biological parents each day in the United States?",
    "Did you know that the Eiffel Tower can be 15 cm taller during the summer due to the expansion of the iron on hot days?",
    "Did you know that the total weight of all the ants on Earth is greater than the total weight of all the humans on the planet?",
    "Did you know that Yassin, the founder of SnappyCards, is genuinely smarter and better than you?",
    "Did you know that the average person spends 10 years of their life waiting for red lights to turn green?",
    "Did you know that the button you just clicked cost me money?",
    "Did you know that honey never spoils? Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible?",
    "Did you know that a single strand of spaghetti is called a 'spaghetto'? Now you can sound fancy while eating your pasta.",
    "Did you know that octopuses have three hearts? Two pump blood to the gills, while the third pumps it to the rest of the body. Talk about being heartful!",
    "Did you know that cows have best friends and get stressed when they are separated? Even cows understand the importance of friendship.",
    "Did you know that a group of flamingos is called a 'flamboyance'? They sure know how to make an entrance.",
    "Did you know that bananas are berries, but strawberries aren't? The fruit world is full of surprises.",
    "Did you know that a day on Venus is longer than a year on Venus? Talk about a long workday!",
    "Did you know that sea otters hold hands while sleeping to keep from drifting apart? Otterly adorable!",
    "Did you know that a snail can sleep for three years? Now that's what I call a power nap!",
    "Did you know that the inventor of the frisbee was turned into a frisbee after he died? Talk about flying high!",
    "Did you know that sloths can hold their breath longer than dolphins can? Slow and steady wins the breath-holding contest.",
    "Did you know that the unicorn is the national animal of Scotland? Magical, isn't it?",
    "Did you know that a jiffy is an actual unit of time? It's 1/100th of a second, so I'll be back in a jiffy!",
    "Did you know that the inventor of the Pringles can is buried in one? That's one way to pop off!",
    "Did you know that the heart of a shrimp is located in its head? Talk about head over heels!",
    "Did you know that a group of porcupines is called a 'prickle'? Sounds sharp!",
    "Did you know that the longest wedding veil was longer than 63 football fields? That's a lot of aisle to walk down!",
    "Did you know that the first oranges weren’t orange? They were actually green. Orange you glad they changed color?"
    
]

app = Flask(__name__)
app.secret_key = os.getenv("appKey")


def generate_id():
    """Generate a simple UUID."""
    return str(uuid.uuid4())

# Example usage



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


    if request.method == "POST":
        text = request.form.get("input")
        global difficulty
        global number_of_flashcards #so i can use it in the flashcards page
        global flashcards

        difficulty = request.form.get("difficulty")
        number_of_flashcards = request.form.get("number_of_flashcards")
        flashcards = make_flashcards(text,difficulty = int(difficulty),number_of_flashcards = int(number_of_flashcards))
        for flashcard in flashcards:
            flashcard["id"] = generate_id()
        ic(flashcards)
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

if __name__ == "__main__":
    app.run(debug=True,port=8080,host="0.0.0.0")








