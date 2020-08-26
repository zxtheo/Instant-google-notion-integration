# Instant-google-notion-integration

### Connect Google Calendar and Notion together with insant updates on both sides (with some server link clicks)

#### Required:

* client-secret.json --> aquired from getting your oauth key from Google Cloud

* secrets.json

  ```
  }
    "notion-client-token-V2":"",
    "notion-calendar-view":"",
    "calendars":[]
  }
  ```
  
    notion-client-token-V2 --> aquired by looking at cookies on active notion browser session
    
    notion-calendar-view --> aquired by putting your callendar into task view and getting the link of that block
    
    calendars --> list of google calendars you want to read and write to
    
 * Notion-py library installed 
     https://github.com/jamalex/notion-py
     
   ensuring that:
   ```python
   # In collection.py L154 is line below
              if view is None or isinstance(view, CalendarView):
     ```
  * making sure your notion calendar has these columns:
  
    ![notion table columns](https://github.com/zxtheo/Instant-google-notion-integration/blob/master/callendar%20view.PNG)
    
    and ensure that the options for "calendar" are set to the calendars previously set in secrets.json
