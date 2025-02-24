import datetime
import threading
import vosk
import pyaudio
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
from groq_llama import gen
from assistantTools import get_events, get_free_slots_today, get_free_slots_week, get_todays_events, format_time, get_weeks_events

# Google Calendar API setup
SERVICE_ACCOUNT_FILE = "calendar-access.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=creds)

# Here I have downloaded this model to my PC, extracted the files 
# and saved it in local directory
# Set the model path
model_path = "vosk-model-en-us-0.42-gigaspeech"
# Initialize the model with model-path
model = vosk.Model(model_path)

def show_directions():
    """Creates a separate window to display directions."""
    directions_window = tk.Toplevel(root)
    directions_window.title("Voice Assistant Directions")

    directions_text = (
        "Directions:\n"
        "- Say 'When am I free this week?' to get your available time slots.\n"
        "- Say 'When am I free today?' to get today's free time.\n"
        "- Say 'What events do I have today?' to see your schedule.\n"
        "- Say 'What events do I have this week?' for weekly events.\n"
        "- Say 'What events do I have coming up?' for upcoming events.\n"
        "- Say 'Question' to ask a general question.\n"
        "- Say 'Terminate' to stop the assistant.\n"
        "- Have Fun!"
    )

    text_box = tk.Text(directions_window, wrap=tk.WORD, height=20, width=50)
    text_box.insert(tk.END, directions_text)
    text_box.config(state=tk.DISABLED)  # Make text read-only
    text_box.pack(pady=10)

def run_assistant():
    text_display.insert(tk.END, "Hi I am your built in Voice AI Assistant - Rahul\n")
    text_display.insert(tk.END, "Feel free to speak your notes or your ideas!\n")
    text_display.insert(tk.END, "Listening for speech... Say 'Terminate' to stop.\n")
    rec = vosk.KaldiRecognizer(model, 16000)

    # Open the microphone stream
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=2048)


    # Open a text file in write mode using a 'with' block
    while True:
        data = stream.read(4096, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            recognized_text = result["text"]
            text_display.insert(tk.END, recognized_text + "\n")
            text_display.see(tk.END)  # Auto-scroll
            print(recognized_text)
            
            if "question" in recognized_text.lower():
                text_display.insert(tk.END, "Please ask your question...\n")
                print("Please ask your question...")
                while True:
                    data = stream.read(4096)
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        question_text = result["text"]
                        print(f"You asked: {question_text}")
                        response = gen(question_text)
                        text_display.insert(tk.END, f"AI Answer: {response}\n")
                        print(f"AI Answer: {response}")
                        break

            if "when am i free this week" in recognized_text.lower():
                free_slots = get_free_slots_week()
                if free_slots:
                    free_slots_by_day = {}
                    text_display.insert(tk.END, "You are free at the following times this week\n")
                    print("You are free at the following times this week:")
                    for start, end in free_slots:
                        day = start.strftime("%A, %B %d")
                        time_range = f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"
                        if day not in free_slots_by_day:
                            free_slots_by_day[day] = []
                        free_slots_by_day[day].append(time_range)
                        
                    for day, slots in free_slots_by_day.items():
                        formatted_slots = ", ".join(slots)
                        text_display.insert(tk.END, f"{day}: {formatted_slots}\n")
                        print(f"{day}: {formatted_slots}")
                else:
                    text_display.insert(tk.END, "You have no free time this week\n")
                    print("You have no free time this week.")
                    
            elif "when am i free today" in recognized_text.lower():
                free_slots = get_free_slots_today()
                if free_slots:
                    text_display.insert(tk.END, "You are free at the following times today\n")
                    print("You are free at the following times today:")
                    for start, end in free_slots:
                        text_display.insert(tk.END, f"{format_time(start)} - {format_time(end)}\n")
                        print(f"{format_time(start)} - {format_time(end)}")
                        
            elif "what events do i have today" in recognized_text.lower():
                events_today = get_todays_events()
                text_display.insert(tk.END, "✅ Today's Events:\n")
                print("✅ Today's Events:")
                for event in events_today:
                    event_summary = event.get("summary", "No Title")
                    start_time = event.get("start_time", "Unknown Time")
                    start_time_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S %Z") #convert to DT object to call function
                    formatted_time = format_time(start_time_dt)
                    text_display.insert(tk.END, f"- {event_summary} at {formatted_time}\n")
                    print(event)

            elif "what events do i have this week" in recognized_text.lower():
                events_this_week = get_weeks_events()
                text_display.insert(tk.END, "✅ Events This Week:\n")
                print("✅ Events This Week:")
                for event in events_this_week:
                    if event is None:
                        return "Invalid time"
                    event_summary = event.get("summary", "No Title")
                    start_time = event.get("start_time", "Unknown Time")
                    start_time_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S %Z") #convert to DT object to call function
                    formatted_time = format_time(start_time_dt)
                    text_display.insert(tk.END, f"- {event_summary} at {formatted_time}\n")
                    print(event)

            elif "what events do i have coming up" in recognized_text.lower():
                upcoming_events = get_events()
                text_display.insert(tk.END, "✅ Upcoming Events:\n")
                print("✅ Upcoming Events:")
                for event in upcoming_events: 
                    event_summary = event.get("summary", "No Title")
                    start_time = event.get("start_time", "Unknown Time")
                    start_time_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S %Z") #convert to DT object to call function
                    formatted_time = format_time(start_time_dt)
                    text_display.insert(tk.END, f"- {event_summary} at {formatted_time}\n")
                    print(event)
                    
            elif "terminate" in recognized_text.lower():
                text_display.insert(tk.END, "Termination keyword detected. Stopping...\n")
                print("Termination keyword detected. Stopping...")
                break
            
    # Stop and close the stream
    stream.stop_stream()
    stream.close()

    # Terminate the PyAudio object
    p.terminate()
    
def start_assistant():
    thread = threading.Thread(target=run_assistant)
    thread.start()

root = tk.Tk()
root.title("Voice Assistant")
root.configure(bg="#1a1524")

title_label = tk.Label(root, text="Voice Assistant", font=("Arial", 18, "bold"), bg="#f0f0f0", fg="#333")
title_label.pack(pady=10)

style = ttk.Style()
style.configure("TButton", font=("Arial", 12), padding=10)

button = tk.Button(root, text="I am ready to speak", command=start_assistant)
button.pack(pady=10)

directions_button = tk.Button(root, text="Show Directions", command=show_directions)
directions_button.pack(pady=5)

text_frame = tk.Frame(root, bg="#1a1524")
text_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

text_display = tk.Text(text_frame, wrap=tk.WORD, height=20, width=40, font=("Arial", 12), bg="white", fg="black")
text_display.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

root.mainloop()
