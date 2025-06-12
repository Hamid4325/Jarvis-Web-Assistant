
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import groq
import pyttsx3
import speech_recognition as sr
import sys
import requests
# import pyautogui
import os
import webbrowser
import time
import pyjokes
from groq import Groq
import queue
import webbrowser

# Initialize Flask app
app = Flask(__name__, template_folder='.')

# Initialize pyttsx3 engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 200)

# Create a queue to store text messages
text_queue = queue.Queue()

def talk(text, callback=None):
  """Speaks the text and optionally calls a callback function."""
  engine.say(text)
  if callback:
    engine.runAndWait()

# Initialize Groq client
api_key = 'YOUR API'
client = Groq(api_key=api_key)

# List to store chat messages
messages = [
    {'role': 'system', 'content': 'ROLE YOU WANT TO ASSING IT OR MESSAGES TO REMEMBER BRFORE ANSWERING'}
]

# Function to add messages to the chat
def add_messages(role, content):
    messages.append({"role": role, "content": content})

# Function to interact with GPT model
# Function to interact with GPT model
def GPT(messages, *args):
    # Check if args is empty and return a default response if true
    if not args:
        return "No input provided for GPT function."

    new_messages = [{'role': 'user', "content": ''.join(args)}]
    messages.extend(new_messages)
    chat_completion = client.chat.completions.create(
         messages=messages,
        #  model="mixtral-8x7b-32768"
        #  model="mistral-saba-24b"
        # model="llama-3.3-70b-versatile"
         #model="deepseek-r1-distill-llama-70b"
         model="gemma2-9b-it"
    )
    response = chat_completion.choices[0].message.content
    ms = ''.join(response)
    print(ms.encode(sys.stdout.encoding, 'backslashreplace').decode(sys.stdout.encoding), end="", flush=True)
    add_messages("assistant", response)
    return response


def get_transcript(video_url):
    try:
        video_id = video_url.split("v=")[1]
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = ""

        for entry in transcript:
            text += entry["text"] + ""

        return text
    except Exception as e:
        return str(e)


# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for processing user query
@app.route('/process_query', methods=['POST'])
def process_query():
    query = request.form['query']
    url = None
    if "https://www.youtube.com/watch?v=" in query:
        start_index = query.find("https://www.youtube.com/watch?v=")
        query = query[start_index:].strip()
        query = query[:start_index].lower() + query[start_index:]
    else:
        query = query.lower()

    try:
        response = run_jarvis(query)
        talk(response)
        return jsonify({'response': response})
    except groq.InternalServerError:
        return "Sorry, Jarvis is currently unavailable. Please try again later.", 503
    # except Exception as e:
    #     return str(e), 500

# Route to handle speech input
@app.route('/process_speech', methods=['POST'])
def process_speech():
    audio_file = request.files['audio_data']
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source) # type: ignore

    try:
        query = recognizer.recognize_google(audio) # type: ignore
        response = run_jarvis(query)
        talk(response)  # Speak the response
        return jsonify({'response': response})
    except sr.UnknownValueError:
        return jsonify({'response': "Sorry, I didn't understand that."})
    except sr.RequestError:
        return jsonify({'response': "Sorry, my speech service is unavailable."})
    except Exception as e:
        return jsonify({'response': str(e)}), 500


# Function to handle user queries
def run_jarvis(query):
    """Run Jarvis based on the user query."""
    response = ""

    if 'hello ' in query or 'hi ' in query:
        response = 'Hi sir, how are you?'

    elif 'exit' in query:
        response = 'Goodbye!'
        sys.exit()

    elif 'youtube' in query:
        webbrowser.open_new_tab("https://www.youtube.com/")

    elif "know" in query or 'solve' in query or 'gpt' in query or 'suggest' in query or 'help' in query or "explain" in query:
        response = GPT(messages, query)
        print()

    elif 'joke' in query:
        jokes = pyjokes.get_joke()
        print(jokes)
        response = jokes

    elif "https://www.youtube.com/watch?v=" in query:
        video_url = query
        transcript = get_transcript(video_url)
        if transcript:
            # print(transcript)
            response = GPT(messages, transcript)# + "* explain this script in short. *"
        else:
            response = "Transcript is empty."

    elif 'remember that' in query:
        rememberMessage = query.replace('remember that', '')
        response = f'you told me to remember that {rememberMessage}'
        with open('remember.txt', 'a') as remember:
            remember.write(rememberMessage)

    elif 'what do you remember' in query:
        if not open('remember.txt', 'r'):
             response = "File do not exist."
        with open('remember.txt', 'r') as remember:
            response = 'you told me to remember ' + remember.read()

    elif 'clear remember file' in query:
        with open('remember.txt', 'w') as file:
            file.write('')
        response = 'Done sir! everything I remember has been deleted.'

    elif 'shutdown' in query:
        response = 'Closing the pc in 3. 2. 1'
        os.system("shutdown /s /t 1")

    elif 'restart' in query:
        response = 'Restarting the pc in 3. 2. 1'
        os.system("shutdown /r /t 1")

    elif query == "":
        response = "Please enter some query first."

    else:
        response = GPT(messages, query)
        print()

    return response


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
