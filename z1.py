import requests
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer
import json
import os

# Инициализация TTS движка
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    if 'english' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

def speak(text):
    engine.say(text)
    engine.runAndWait()

# Функция для получения шутки
def get_joke():
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Any?safe-mode")
        response.raise_for_status()  # Проверка на ошибки HTTP
        joke_data = response.json()
        return joke_data
    except requests.exceptions.HTTPError as http_err:
        speak(f"HTTP error occurred: {http_err}")
    except Exception as err:
        speak(f"An error occurred: {err}")
    return None

# Инициализация модели распознавания речи
if not os.path.exists("vosk-model-small-en-us-0.15"):
    speak("The speech recognition model path does not exist.")
    exit(1)

model = Model("vosk-model-small-en-us-0.15")
rec = KaldiRecognizer(model, 16000)

# Инициализация PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
stream.start_stream()

# Цикл для распознавания речи и обработки команд
while True:
    data = stream.read(4096, exception_on_overflow=False)
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        text = result.get("text", "").lower()  # Приведение распознанного текста к нижнему регистру
        print(f"Recognized words: {text}")  # Вывод распознанных слов в консоль

        # Обработка команд
        if "create" in text:
            joke_data = get_joke()
            if joke_data:
                if joke_data['type'] == 'twopart':
                    speak(f"Here is a two-part joke: {joke_data['setup']} ... {joke_data['delivery']}")
                else:
                    speak(f"Here is a joke: {joke_data['joke']}")
        elif "type" in text:
            if 'joke_data' in locals():
                if joke_data['type'] == 'twopart':
                    speak("This is a two-part joke.")
                else:
                    speak("This is a single-part joke.")
            else:
                speak("No joke has been created yet.")
        elif "read" in text:
            if 'joke_data' in locals():
                if joke_data['type'] == 'twopart':
                    speak(f"{joke_data['setup']} ... {joke_data['delivery']}")
                else:
                    speak(joke_data['joke'])
            else:
                speak("No joke has been created yet.")
        elif "category" in text:
            if 'joke_data' in locals():
                speak(f"The category of this joke is: {joke_data['category']}")
            else:
                speak("No joke has been created yet.")
        elif "save" in text:
            if 'joke_data' in locals():
                with open('jokes.txt', 'a') as file:
                    if joke_data['type'] == 'twopart':
                        file.write(f"{joke_data['setup']} ... {joke_data['delivery']}\n")
                    else:
                        file.write(f"{joke_data['joke']}\n")
                speak("Joke added to the file.")
            else:
                speak("No joke has been created yet.")
        else:
            speak("Command not recognized. Please try again.")
