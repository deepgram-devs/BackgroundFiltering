import datetime
from openai_chat import gen
import pytz
from google_oauth import get_calendar_service

# Remove service account imports and setup
# from google.oauth2 import service_account
# from googleapiclient.discovery import build

# Global timezone variable (default to user's local timezone)
user_timezone = None

def get_user_timezone():
    """Get the user's selected timezone, default to local timezone"""
    global user_timezone
    if user_timezone:
        return user_timezone
    else:
        # Default to local timezone
        return datetime.datetime.now().astimezone().tzinfo

def set_user_timezone(timezone_str):
    """Set the user's preferred timezone"""
    global user_timezone
    try:
        user_timezone = pytz.timezone(timezone_str)
        print(f"✅ Timezone set to: {timezone_str}")
        return True
    except Exception as e:
        print(f"❌ Error setting timezone: {e}")
        return False

def get_calendar_service_safe():
    """Get calendar service with error handling"""
    service = get_calendar_service()
    if not service:
        print("Error: Not authenticated with Google Calendar")
        return None
    return service

def parse_datetime_safely(datetime_str):
    """Safely parse datetime strings from Google Calendar API"""
    if not datetime_str:
        return None
    
    try:
        # Handle different datetime formats from Google Calendar
        if 'T' in datetime_str:
            # Regular datetime with timezone
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str.replace('Z', '+00:00')
            return datetime.datetime.fromisoformat(datetime_str)
        else:
            # All-day event (date only)
            date_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%d')
            # Make it timezone-aware (UTC)
            return date_obj.replace(tzinfo=pytz.UTC)
    except Exception as e:
        print(f"Error parsing datetime '{datetime_str}': {e}")
        return None

def get_free_slots_today():
    """Fetches today's events and calculates free slots correctly."""
    service = get_calendar_service_safe()
    if not service:
        return []
        
    # Use UTC timezone consistently
    utc = pytz.UTC
    now = datetime.datetime.now(utc)

    # Define start and end of today in UTC
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

    start_of_day_str = start_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_of_day_str = end_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day_str,
            timeMax=end_of_day_str,
            maxResults=100,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])

        free_slots = []
        last_end = start_of_day

        for event in events:
            start_time_str = event["start"].get("dateTime", event["start"].get("date"))
            end_time_str = event["end"].get("dateTime", event["end"].get("date"))

            start_time = parse_datetime_safely(start_time_str)
            end_time = parse_datetime_safely(end_time_str)

            if not start_time or not end_time:
                continue

            # Ensure timezone awareness
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=utc)

            # Handle all-day events
            if not event["start"].get("dateTime"):  # All-day event
                start_time = start_of_day
                end_time = end_of_day

            if start_time > last_end:
                free_slots.append((last_end, start_time))

            last_end = max(last_end, end_time)

        if last_end < end_of_day:
            free_slots.append((last_end, end_of_day))

        return free_slots
    
    except Exception as e:
        print(f"Error fetching free slots: {e}")
        return []

def get_free_slots_week():
    """Fetches week's events and calculates free slots."""
    service = get_calendar_service_safe()
    if not service:
        return []
        
    # Use UTC timezone consistently
    utc = pytz.UTC
    now = datetime.datetime.now(utc)

    # Calculate start of week (Monday)
    start_of_week = now - datetime.timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    start_of_week_str = start_of_week.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_of_week_str = end_of_week.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_week_str,
            timeMax=end_of_week_str,
            maxResults=50,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])

        free_slots = []
        last_end = start_of_week

        for event in events:
            start_time_str = event["start"].get("dateTime", event["start"].get("date"))
            end_time_str = event["end"].get("dateTime", event["end"].get("date"))

            start_time = parse_datetime_safely(start_time_str)
            end_time = parse_datetime_safely(end_time_str)

            if not start_time or not end_time:
                continue

            # Ensure timezone awareness
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=utc)

            if start_time > last_end:
                free_slots.append((last_end, start_time))

            last_end = max(last_end, end_time)

        if last_end < end_of_week:
            free_slots.append((last_end, end_of_week))

        return free_slots
    
    except Exception as e:
        print(f"Error fetching weekly free slots: {e}")
        return []

def format_time(dt):
    """Formats a datetime object to a readable time string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    
    # Convert to local timezone for display
    local_tz = datetime.datetime.now().astimezone().tzinfo
    local_dt = dt.astimezone(local_tz)
    return local_dt.strftime("%I:%M %p")

def format_event_time(event_time_str):
    """Format event time string consistently in MM/DD/YYYY format"""
    if not event_time_str:
        return "Unknown Time"
    
    try:
        dt = parse_datetime_safely(event_time_str)
        if dt:
            # Convert to user's timezone
            user_tz = get_user_timezone()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            local_dt = dt.astimezone(user_tz)
            
            # Format as MM/DD/YYYY HH:MM AM/PM
            return local_dt.strftime("%m/%d/%Y %I:%M %p")
        return event_time_str
    except:
        return event_time_str

def get_events():
    """Fetches and returns a list of upcoming events."""
    service = get_calendar_service_safe()
    if not service:
        return []
        
    utc = pytz.UTC
    now = datetime.datetime.now(utc)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now_str,
            maxResults=5,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        event_list = []

        for event in events:
            start_time_str = event["start"].get("dateTime", event["start"].get("date"))
            formatted_time = format_event_time(start_time_str)
            
            event_list.append({
                "summary": event.get("summary", "No Title"),
                "start_time": formatted_time
            })

        return event_list
    except Exception as e:
        print(f"Error fetching events: {e}")
        return []

def get_todays_events():
    """Fetches and returns today's events in a list."""
    service = get_calendar_service_safe()
    if not service:
        return []
        
    utc = pytz.UTC
    now = datetime.datetime.now(utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

    start_of_day_str = start_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_of_day_str = end_of_day.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day_str,
            timeMax=end_of_day_str,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        event_list = []

        for event in events:
            start_time_str = event["start"].get("dateTime", event["start"].get("date"))
            formatted_time = format_event_time(start_time_str)
            
            event_list.append({
                "summary": event.get("summary", "No Title"),
                "start_time": formatted_time
            })

        return event_list
    except Exception as e:
        print(f"Error fetching today's events: {e}")
        return []

def get_weeks_events():
    """Fetches and returns this week's events as a list."""
    service = get_calendar_service_safe()
    if not service:
        return []
        
    utc = pytz.UTC
    now = datetime.datetime.now(utc)
    
    # Calculate start of week (Monday)
    start_of_week = now - datetime.timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)

    start_of_week_str = start_of_week.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_of_week_str = end_of_week.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_week_str,
            timeMax=end_of_week_str,
            maxResults=50,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        event_list = []

        for event in events:
            start_time_str = event["start"].get("dateTime", event["start"].get("date"))
            formatted_time = format_event_time(start_time_str)
            
            event_list.append({
                "summary": event.get("summary", "No Title"),
                "start_time": formatted_time
            })

        return event_list
    except Exception as e:
        print(f"Error fetching week's events: {e}")
        return []
