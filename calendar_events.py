import datetime
import pytz
import re
import json
from dateutil import parser
from dateutil.relativedelta import relativedelta
from openai_chat import gen
from google_oauth import get_calendar_service
from assistantTools import get_user_timezone

def get_calendar_service_safe():
    """Get calendar service with error handling"""
    service = get_calendar_service()
    if not service:
        print("Error: Not authenticated with Google Calendar")
        return None
    return service

def parse_natural_date(date_string):
    """Parse natural language dates like 'tomorrow', 'next Friday', etc."""
    today = datetime.date.today()
    date_string = date_string.lower().strip()
    
    # Handle relative dates
    if 'tomorrow' in date_string:
        return today + datetime.timedelta(days=1)
    elif 'today' in date_string:
        return today
    elif 'next week' in date_string:
        return today + datetime.timedelta(weeks=1)
    elif 'next month' in date_string:
        return today + relativedelta(months=1)
    
    # Handle day names
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(days):
        if day in date_string:
            days_ahead = i - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            if 'next' in date_string:
                days_ahead += 7
            return today + datetime.timedelta(days=days_ahead)
    
    # Try to parse with dateutil
    try:
        parsed_date = parser.parse(date_string, fuzzy=True)
        return parsed_date.date()
    except:
        return None

def create_calendar_event(summary, description="", location="", start_datetime=None, end_datetime=None, attendees=None):
    """
    Create a new calendar event
    
    Args:
        summary (str): Event title
        description (str): Event description
        location (str): Event location
        start_datetime (datetime): Start time
        end_datetime (datetime): End time
        attendees (list): List of email addresses
    
    Returns:
        dict: Created event details or None if failed
    """
    service = get_calendar_service_safe()
    if not service:
        return None
    
    try:
        # Get user's timezone
        user_tz = get_user_timezone()
        
        # Default to 1-hour event if no end time provided
        if start_datetime and not end_datetime:
            end_datetime = start_datetime + datetime.timedelta(hours=1)
        
        # Convert to user's timezone and RFC3339 format
        if start_datetime:
            # If no timezone info, assume it's in user's timezone
            if start_datetime.tzinfo is None:
                start_datetime = user_tz.localize(start_datetime)
            if end_datetime.tzinfo is None:
                end_datetime = user_tz.localize(end_datetime)
            start_rfc = start_datetime.isoformat()
            end_rfc = end_datetime.isoformat()
            timezone_name = str(user_tz)
        else:
            # Default to next hour if no time specified
            now = datetime.datetime.now(user_tz)
            start_datetime = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
            end_datetime = start_datetime + datetime.timedelta(hours=1)
            start_rfc = start_datetime.isoformat()
            end_rfc = end_datetime.isoformat()
            timezone_name = str(user_tz)
        
        # Build event object according to Google Calendar API
        event = {
            'summary': summary,
            'description': description,
            'location': location,
            'start': {
                'dateTime': start_rfc,
                'timeZone': timezone_name,
            },
            'end': {
                'dateTime': end_rfc,
                'timeZone': timezone_name,
            },
        }
        
        # Add attendees if provided
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Create the event using Google Calendar API
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all' if attendees else 'none'
        ).execute()
        
        print(f"✅ Event created: {created_event.get('summary')}")
        print(f"🔗 Event link: {created_event.get('htmlLink')}")
        
        return {
            'id': created_event.get('id'),
            'summary': created_event.get('summary'),
            'start_time': created_event.get('start', {}).get('dateTime'),
            'end_time': created_event.get('end', {}).get('dateTime'),
            'html_link': created_event.get('htmlLink')
        }
        
    except Exception as e:
        print(f"❌ Error creating event: {e}")
        return None

def parse_event_from_speech(speech_text):
    """
    Parse event details from natural speech using AI
    
    Args:
        speech_text (str): Natural language event description
    
    Returns:
        dict: Parsed event details
    """
    prompt = f"""
    Parse the following speech into calendar event details. Extract:
    - title/summary
    - date (convert relative dates like 'tomorrow', 'next Friday' to actual dates)
    - start time
    - end time (if mentioned, otherwise assume 1 hour duration)
    - location (if mentioned)
    - attendees/people (if mentioned)
    - description/notes
    
    Today is {datetime.date.today().strftime('%A, %B %d, %Y')}.
    
    Speech: "{speech_text}"
    
    Respond in JSON format:
    {{
        "title": "event title",
        "date": "YYYY-MM-DD",
        "start_time": "HH:MM",
        "end_time": "HH:MM",
        "location": "location or null",
        "attendees": ["email1", "email2"] or null,
        "description": "additional details or null"
    }}
    """
    
    try:
        response = gen(prompt)
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            event_data = json.loads(json_match.group())
            return event_data
        else:
            print("❌ Could not parse AI response as JSON")
            return None
    except Exception as e:
        print(f"❌ Error parsing event from speech: {e}")
        return None

def create_event_from_speech(speech_text):
    """
    Create a calendar event from natural language speech
    
    Args:
        speech_text (str): Natural language event description
    
    Returns:
        dict: Created event details or None if failed
    """
    # Parse the speech
    event_data = parse_event_from_speech(speech_text)
    if not event_data:
        return None
    
    try:
        # Convert parsed data to datetime objects
        event_date = datetime.datetime.strptime(event_data['date'], '%Y-%m-%d').date()
        start_time = datetime.datetime.strptime(event_data['start_time'], '%H:%M').time()
        end_time = datetime.datetime.strptime(event_data['end_time'], '%H:%M').time()
        
        start_datetime = datetime.datetime.combine(event_date, start_time)
        end_datetime = datetime.datetime.combine(event_date, end_time)
        
        # Create the event
        return create_calendar_event(
            summary=event_data['title'],
            description=event_data.get('description', ''),
            location=event_data.get('location', ''),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            attendees=event_data.get('attendees')
        )
        
    except Exception as e:
        print(f"❌ Error creating event from parsed data: {e}")
        return None

def find_events_by_title(title_search):
    """
    Find events by searching their titles
    
    Args:
        title_search (str): Search term for event titles
    
    Returns:
        list: List of matching events
    """
    service = get_calendar_service_safe()
    if not service:
        return []
    
    try:
        # Search for events in the next 30 days
        utc = pytz.UTC
        now = datetime.datetime.now(utc)
        time_max = now + datetime.timedelta(days=30)
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now.isoformat(),
            timeMax=time_max.isoformat(),
            q=title_search,  # Search query
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        return [{
            'id': event.get('id'),
            'summary': event.get('summary', 'No Title'),
            'start_time': event.get('start', {}).get('dateTime', event.get('start', {}).get('date')),
            'end_time': event.get('end', {}).get('dateTime', event.get('end', {}).get('date')),
            'location': event.get('location', ''),
            'description': event.get('description', '')
        } for event in events]
        
    except Exception as e:
        print(f"❌ Error searching events: {e}")
        return []

def update_calendar_event(event_id, summary=None, description=None, location=None, start_datetime=None, end_datetime=None):
    """
    Update an existing calendar event
    
    Args:
        event_id (str): Event ID to update
        summary (str): New event title
        description (str): New event description  
        location (str): New event location
        start_datetime (datetime): New start time
        end_datetime (datetime): New end time
    
    Returns:
        dict: Updated event details or None if failed
    """
    service = get_calendar_service_safe()
    if not service:
        return None
    
    try:
        # Get existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        # Update fields if provided
        if summary:
            event['summary'] = summary
        if description is not None:
            event['description'] = description
        if location is not None:
            event['location'] = location
        if start_datetime:
            utc = pytz.UTC
            if start_datetime.tzinfo is None:
                start_datetime = utc.localize(start_datetime)
            event['start']['dateTime'] = start_datetime.isoformat()
        if end_datetime:
            utc = pytz.UTC
            if end_datetime.tzinfo is None:
                end_datetime = utc.localize(end_datetime)
            event['end']['dateTime'] = end_datetime.isoformat()
        
        # Update the event
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()
        
        print(f"✅ Event updated: {updated_event.get('summary')}")
        return {
            'id': updated_event.get('id'),
            'summary': updated_event.get('summary'),
            'start_time': updated_event.get('start', {}).get('dateTime'),
            'end_time': updated_event.get('end', {}).get('dateTime'),
            'html_link': updated_event.get('htmlLink')
        }
        
    except Exception as e:
        print(f"❌ Error updating event: {e}")
        return None

def delete_calendar_event(event_id):
    """
    Delete a calendar event
    
    Args:
        event_id (str): Event ID to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    service = get_calendar_service_safe()
    if not service:
        return False
    
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"✅ Event deleted successfully")
        return True
    except Exception as e:
        print(f"❌ Error deleting event: {e}")
        return False

def parse_move_request(speech_text):
    """
    Parse move/reschedule request using AI
    
    Args:
        speech_text (str): Natural language move request
    
    Returns:
        dict: Parsed move request with event_search and new_time
    """
    prompt = f"""
    Parse this event move/reschedule request. Extract:
    - The event to find (keywords from the event title)
    - The new date/time to move it to
    
    Today is {datetime.date.today().strftime('%A, %B %d, %Y')}.
    
    Speech: "{speech_text}"
    
    Examples:
    "Move meeting to tomorrow 2 PM" -> {{"event_search": "meeting", "new_time": "tomorrow 2 PM"}}
    "Reschedule dentist appointment to next Friday 10 AM" -> {{"event_search": "dentist", "new_time": "next Friday 10 AM"}}
    
    Respond in JSON format:
    {{
        "event_search": "keywords to find the event",
        "new_time": "new date and time"
    }}
    """
    
    try:
        response = gen(prompt)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"❌ Error parsing move request: {e}")
        return None

def move_event_to_new_time(event, new_time_str):
    """
    Move a single event to a new time
    
    Args:
        event (dict): Event dictionary with 'id' key
        new_time_str (str): Natural language description of new time
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Parse the new time using AI
        # Create a fake event description to parse the new time
        fake_description = f"event at {new_time_str}"
        parsed_time = parse_event_from_speech(fake_description)
        
        if not parsed_time:
            return False
        
        # Convert to datetime objects
        event_date = datetime.datetime.strptime(parsed_time['date'], '%Y-%m-%d').date()
        start_time = datetime.datetime.strptime(parsed_time['start_time'], '%H:%M').time()
        end_time = datetime.datetime.strptime(parsed_time['end_time'], '%H:%M').time()
        
        new_start = datetime.datetime.combine(event_date, start_time)
        new_end = datetime.datetime.combine(event_date, end_time)
        
        # Update the event
        result = update_calendar_event(
            event['id'],
            start_datetime=new_start,
            end_datetime=new_end
        )
        
        return result is not None
        
    except Exception as e:
        print(f"❌ Error moving event: {e}")
        return False