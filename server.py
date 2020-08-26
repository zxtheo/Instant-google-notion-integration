from flask import Flask
from main import *
app = Flask(__name__)

@app.route("/new_notion_events")
def make_new_notion_events():
    return ("<p>" + '</p><p>'.join(create_new_notion_events()))

@app.route("/update_google_callendar_events")
def update_google_callendar_events():
    return ("<p>" + '</p><p>'.join(update_google_calendar_events()))
    

if __name__ == "__main__":
    app.run()