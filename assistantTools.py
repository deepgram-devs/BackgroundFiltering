
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import speech_recognition as sr
from groq_llama import gen

# Google Calendar API setup
SERVICE_ACCOUNT_FILE = "calendar-access.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=creds)


def get_free_slots_today():
    """Fetches today's events and calculates free slots correctly."""
    now = datetime.datetime.now(datetime.timezone.utc)

    # Define start and end of today (keeping them as datetime objects)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

    start_of_day_str = start_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_of_day_str = end_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        events_result = service.events().list(
            calendarId="rahul.chavali1@gmail.com",
            timeMin=start_of_day_str,
            timeMax=end_of_day_str,
            maxResults=100,  # Ensuring all events are fetched
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])

        free_slots = []
        last_end = start_of_day  # Keep as datetime object

        for event in events:
            start_time = event["start"].get("dateTime", event["start"].get("date"))
            end_time = event["end"].get("dateTime", event["end"].get("date"))

            if "T" not in start_time:  # Handling all-day events
                start_time = start_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")
                end_time = end_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")

            start_time = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_time = datetime.datetime.fromisoformat(end_time.replace("Z", "+00:00"))

            if start_time > last_end:
                free_slots.append((last_end, start_time))

            last_end = max(last_end, end_time)

        if last_end < end_of_day:
            free_slots.append((last_end, end_of_day))

        return free_slots
    
    except Exception as e:
        print("Error fetching free slots:", e)
        return []

def get_free_slots_week():
    """Fetches weeks's events and calculates free slots."""
    now = datetime.datetime.now(datetime.timezone.utc)

    
    start_of_week = now - datetime.timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    start_of_week = start_of_week.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_of_week = end_of_week.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        events_result = service.events().list(
            calendarId="rahul.chavali1@gmail.com",
            timeMin=start_of_week,
            timeMax=end_of_week,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])

        free_slots = []
        last_end = datetime.datetime.fromisoformat(start_of_week.replace("Z", "+00:00"))

        for event in events:
            start_time = event["start"].get("dateTime", event["start"].get("date"))
            start_time = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00"))

            end_time = event["end"].get("dateTime", event["end"].get("date"))
            end_time = datetime.datetime.fromisoformat(end_time.replace("Z", "+00:00"))

            if start_time > last_end:
                free_slots.append((last_end, start_time))

            last_end = max(last_end, end_time)

        end_of_week_dt = datetime.datetime.fromisoformat(end_of_week.replace("Z", "+00:00"))
        if last_end < end_of_week_dt:
            free_slots.append((last_end, end_of_week_dt))

        return free_slots
    
    except Exception as e:
        print("Error fetching free slots:", e)
        return []


def format_time(dt):
    """Formats a datetime object to a readable time string."""
    return dt.strftime("%I:%M %p")


def get_events():
    """Fetches and returns a list of upcoming events."""
    now = datetime.datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(
        calendarId="rahul.chavali1@gmail.com",
        timeMin=now,
        maxResults=5,  # 5 events for events coming up 
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])
    event_list = []

    for event in events:
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        if "dateTime" in event["start"]:
            start_time_utc = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z")
            local_time = start_time_utc.astimezone(datetime.datetime.now().astimezone().tzinfo)
            start_time = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        event_list.append({"summary": event["summary"], "start_time": start_time})

    return event_list


def get_todays_events():
    """Fetches and returns today's events in a list."""
    now = datetime.datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="rahul.chavali1@gmail.com",
        timeMin=start_of_day,
        timeMax=end_of_day,
        maxResults=20,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])
    event_list = []

    for event in events:
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        if "dateTime" in event["start"]:
            start_time_utc = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z")
            local_time = start_time_utc.astimezone(datetime.datetime.now().astimezone().tzinfo)
            start_time = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        event_list.append({"summary": event["summary"], "start_time": start_time})

    return event_list


def get_weeks_events():
    """Fetches and returns this week's events as a list."""
    now = datetime.datetime.utcnow()
    start_of_week = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)

    start_of_week = start_of_week.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_of_week = end_of_week.strftime("%Y-%m-%dT%H:%M:%SZ")

    events_result = service.events().list(
        calendarId="rahul.chavali1@gmail.com",
        timeMin=start_of_week,
        timeMax=end_of_week,
        maxResults=20,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])
    event_list = []

    for event in events:
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        if "dateTime" in event["start"]:
            start_time_utc = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z")
            local_time = start_time_utc.astimezone(datetime.datetime.now().astimezone().tzinfo)
            start_time = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        event_list.append({"summary": event["summary"], "start_time": start_time})

    return event_list
