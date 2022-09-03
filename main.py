from __future__ import print_function
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import time
import pyttsx3
import speech_recognition as sr
import pytz
import subprocess
# import playsound as ps
# from gtts import gTTS

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTH = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
DAYS_EXT = ["st", "nd", "rd", "th"]

def authenticate_google():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
    except HttpError as error:
        print('An error occurred: %s' % error)

    return service

def get_events(day: int, service):
        # Call the Calendar API
        # now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        # print(f'Getting the upcoming {n} events')
        begin_date = datetime.datetime.combine(day, datetime.datetime.min.time())
        end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
        utc = pytz.UTC
        begin_date = begin_date.astimezone(utc)
        end_date = end_date.astimezone(utc)

        events_result = service.events().list(calendarId='primary', timeMin=begin_date.isoformat(), timeMax=end_date.isoformat(),
                                              singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            speak('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        speak(f"{len(events)} upcoming events on {day}")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event)
            start_time = str(start.split("T")[1].split("+")[0])
            if int(start_time.split(":")[0]) < 12:
                start_time += "am"
            else:
                start_time = str(int(start_time.split(":")[0]) - 12)
                start_time += "pm"

            speak(event['summary'] + " at " + start_time)

def speak(text: str):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    
def get_audio() -> str:
    r = sr.Recognizer()
    with sr.Microphone() as mic:
        print("speak: ")
        r.adjust_for_ambient_noise(mic, duration=0.4)
        audio = r.listen(mic)
        said = ""

        try:
            said = r.recognize_google(audio)
            print(said)
        except Exception as e:
            print("Exceptiion: ", str(e))
    
    return said

def get_date(text: str):
    text = text.lower()
    today = datetime.date.today()

    if "today" in text:
        return today
    
    day, day_of_week, month, year = -1, -1, -1, today.year

    if "tomorrow" in text:
        day = int(str(today).split("-")[2]) + 1
        month = int(str(today).split("-")[1])
        year = int(str(today).split("-")[0])
        return datetime.date(year=year, month=month, day=day)

    for w in text.split():
        if w in MONTH:
            month = MONTH.index(w) + 1
        elif w in DAYS:
            day_of_week = DAYS.index(w)
        elif w.isdigit():
            day = int(w)
        else:
            for ext in DAYS_EXT:
                f = w.find(ext)
                if f > 0:
                    try:
                        day = int(w[:f])
                    except:
                        pass
    
    if month < today.month and month != -1:
        year += 1
    
    if day < today.day and day != -1:
        month += 1
    
    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        diff = day_of_week - current_day_of_week

        if diff < 0:
            diff += 7
            if "next" in text:
                diff += 7
        
        return today + datetime.timedelta(diff)
    if month == -1 or day == -1:
        return None

    return datetime.date(year=year, month=month, day=day)

def create_note(text: str):
    date = datetime.datetime.now()
    filename = str(date).replace(":", "-") + "-note.txt"

    with open(filename, "w") as f:
        f.write(text)

    subprocess.Popen(["notepad.exe", filename])

if __name__ == '__main__':  
    service = authenticate_google()
    print("start")
    # # get_events(3, service)

    text = get_audio().lower()
    CALENDAR_PHRS = ["what do i have", "do i have plans", "am i busy", "my plans"]

    for phrs in CALENDAR_PHRS:
        if phrs in  text:
            date = get_date(text)
            if date:
                get_events(date, service)
            else:
                speak("Try again")
    
    NOTE_PHRS = ["make a note", "write this down", "note it down", "remember this"]

    for phrs in NOTE_PHRS:
        if phrs in text:
            speak("What do you want to note?")
            msg = get_audio().lower()
            if msg:
                create_note(msg)
                speak("Noted")
            else:
                speak("What did you say")