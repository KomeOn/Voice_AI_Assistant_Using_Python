from __future__ import print_function
from curses.ascii import isdigit
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import playsound as ps
import time
import speech_recognition as sr
from gtts import gTTS

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

def get_events(n: int, service):
        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print(f'Getting the upcoming {n} events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=n, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

def speak(text: str):
    tts = gTTS(text=text, lang="en")
    filename = "voice.mp3"
    tts.save(filename)
    ps.playsound(filename)
    
def get_audio() -> str:
    r = sr.Recognizer()
    with sr.Microphone() as mic:
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

    for w in text:
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

if __name__ == '__main__':
    service = authenticate_google()
    get_events(3, service)