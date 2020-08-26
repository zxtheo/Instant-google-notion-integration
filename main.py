import json
from apiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import os.path
import pickle, pprint, time
from datetime import datetime, timedelta
import datetime
from notion.client import NotionClient

### set up constants using secrets
NOTION_CLIENT_TOKEN_V2 = ""
NOTION_CALENDAR_VIEW = ""
GOOGLE_CALENDAR_ID = ""
SCOPES = ""


triggered = False

with open("secrets.json", "r") as secretsFile:
    data = json.load(secretsFile)
    NOTION_CALENDAR_VIEW = data["notion-calendar-view"]
    NOTION_CLIENT_TOKEN_V2 = data["notion-client-token-V2"]
    GOOGLE_CALENDAR_ID = data["google-calendar-id"]
    SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"]



### login flow
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=SCOPES)
if os.path.isfile('./token.pkl'):
    credentials = pickle.load(open("token.pkl", "rb"))
else:
    credentials = flow.run_console()
    
    pickle.dump(credentials, open("token.pkl", "wb"))
service = build("calendar", "v3", credentials=credentials)

### Notion flow
client = NotionClient(token_v2=NOTION_CLIENT_TOKEN_V2)
cv = client.get_collection_view(NOTION_CALENDAR_VIEW)

### get calendar IDs
def get_google_calendar_ids():
    calendar_ids = {}
    result = service.calendarList().list().execute()
    for calendar in result['items']:
        calendar_ids[calendar['summary']] = calendar['id']
    return calendar_ids
calendar_ids = get_google_calendar_ids()


### get calenndar events
def update_notion_events():
    event_list = []
    calendars = ['Deadlines', 'Exams', 'Meetings', 'Study', 'TimeTable', 'Work', "Extra"]
    for calendar in calendars:
        result = service.events().list(calendarId=calendar_ids[calendar], timeZone="Europe/London").execute()
        events = result.get('items', [])
        for event in events:
            now = datetime.datetime.now() - datetime.timedelta(days=10)
            # pprint.pprint(event)
            try:
                date = event['start']['dateTime'].split('T')
                event_date = datetime.datetime.strptime(date[0], "%Y-%m-%d")
            except:
                date = event['start']['date']
                event_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            if event_date > now:
                event_list.append(event)

    notion_events = {}
    for notion_event in cv.collection.get_rows():
        if len(notion_event.google_id) > 0:
            notion_events[notion_event.google_id] = notion_event


    for google_event in event_list:
        try:
            # update events
            pprint.pprint(google_event)
            notion_event = notion_events[google_event['id']]

            notion_event.name = google_event['summary']
            try:
                notion_event.location = google_event['location']
            except:
                pass
            try:
                notion_event.description = google_event['description']
            except:
                pass
            try:
                t = google_event['start']['dateTime'][:19]
                notion_event.date.start =  datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
            except:
                t = google_event['start']['date']
                notion_event.date.start =  datetime.datetime.strptime(date, "%Y-%m-%d")
            try:
                t = google_event['end']['dateTime'][:19]
                notion_event.date.end =  datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
            except:
                t = google_event['end']['date']
                notion_event.date.end =  datetime.datetime.strptime(date, "%Y-%m-%d")

            notion_event.reminder = google_event['reminders']['useDefault']

        except:
            #create new events
            cv.collection.get_rows()
            row = cv.collection.add_row()
            print(row)
            row.name = google_event['summary']
            try:
                row.location = google_event['location']
            except:
                row.location = None
            try:
                row.description = google_event['description']
            except:
                row.description = None
            try:
                t = google_event['start']['dateTime'][:19]
                row.date =  datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
            except:
                t = google_event['start']['date']
                row.date =  datetime.datetime.strptime(t, "%Y-%m-%d")
            try:
                t = google_event['end']['dateTime'][:19]
                duration = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S") - row.date.start
                duration_in_s = duration.total_seconds() 
                row.duration = divmod(duration_in_s, 3600)[0]  
            except:
                t = google_event['end']['date']
                row.duration =  datetime.datetime.strptime(t, "%Y-%m-%d") - row.date.start

            row.reminder = google_event['reminders']['useDefault']
            row.google_id = google_event['id']

    



# pprint.pprint(event_list)

### create calendar event
def create_new_notion_events():
    error_list = {}
    for notion_event in cv.collection.get_rows():
        # pprint.pprint(notion_event)
        
        error_list[notion_event.name] = []
        if len(notion_event.google_id) > 0:
            error_list[notion_event.name].append("LOG: list item: {} -> already in calendar".format(notion_event.name))
            continue
        if notion_event.duration == None:
            notion_event.duration = 23.9 #create all day event
        if notion_event.date == None:
            error_list[notion_event.name].append("ERROR: list item: {} -> has no date".format(notion_event.name))
        if notion_event.calendar == None:
            error_list[notion_event.name].append("ERROR: list item: {} -> has no calendar".format(notion_event.name))
        if len(error_list[notion_event.name]) > 0:
            continue
        
        
        time = False
        try:
            notion_event.date.start.time()
            time = True
        except:
            pass

        if time:
            start_time = notion_event.date.start
        else:
            t = datetime.time(1,0,0)
            d = notion_event.date.start
            start_time = datetime.datetime.combine(d, t)
        end_time = start_time + timedelta(hours=notion_event.duration)
        timezone = 'Europe/London'

        event = {
        'summary': notion_event.name,
        'location': notion_event.location,
        'description': notion_event.description,
        'start': {
            'dateTime': start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
        'reminders': {
            'useDefault': notion_event.reminder,
        },
        }

        eventId = service.events().insert(calendarId=calendar_ids[notion_event.calendar], body=event).execute()
        notion_event.google_id = eventId['id']

    values = [error_list[value] for value in error_list]
    flat_list = [item for sublist in values for item in sublist]
    flat_list.append("LOG: added items to calendar")
    print (flat_list)
    return flat_list

def update_google_calendar_events():
    error_list = {}
    for notion_event in cv.collection.get_rows():
        # pprint.pprint(notion_event.get_all_properties())
        # pprint.pprint(notion_event.duration)
        
        error_list[notion_event.name] = []
        if len(notion_event.google_id) == 0:
            error_list[notion_event.name].append("LOG: list item: {} -> not in calendar".format(notion_event.name))
            continue
        if notion_event.duration == None:
            notion_event.duration = 23.9  #create all day event
        if notion_event.date == None:
            error_list[notion_event.name].append("ERROR: list item: {} -> has no start".format(notion_event.name))
        if notion_event.calendar == None:
            error_list[notion_event.name].append("ERROR: list item: {} -> has no calendar".format(notion_event.name))
        if len(error_list[notion_event.name]) > 0:
            continue
    
        time = False
        try:
            notion_event.date.start.time()
            time = True
        except:
            pass

        if time:
            start_time = notion_event.date.start
        else:
            t = datetime.time(1,0,0)
            d = notion_event.date.start
            start_time = datetime.datetime.combine(d, t)
        

        end_time = start_time + timedelta(hours=notion_event.duration)
        timezone = 'Europe/London'
        
        event = service.events().get(calendarId=calendar_ids[notion_event.calendar], eventId=notion_event.google_id).execute()
        # pprint.pprint(event)
        event['summary'] = notion_event.name,
        event['location'] = notion_event.location,
        event['description'] = notion_event.description,
        event['start'] = {
            'dateTime': start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone}
        event['end'] = {
            'dateTime': end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone}
        event['reminders'] = {
            'useDefault': notion_event.reminder}

        updated_event = service.events().update(calendarId=calendar_ids[notion_event.calendar], eventId=notion_event.google_id,  body=event).execute()
    
    values = [error_list[value] for value in error_list]
    flat_list = [item for sublist in values for item in sublist]
    flat_list.append("LOG: modified calendar")
    print (flat_list)
    return flat_list

# update_google_calendar_events()