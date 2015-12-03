import flask
from flask import render_template
from flask import request
from flask import url_for
import uuid

import json
import logging
import random

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we still need time
from dateutil import tz  # For interpreting local times


# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2   # used in oauth2 flow

# Google API for services 
from apiclient import discovery

# Mongo database
from pymongo import MongoClient

###
# Globals
###
import CONFIG
app = flask.Flask(__name__)

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = CONFIG.GOOGLE_LICENSE_KEY 
APPLICATION_NAME = 'MeetMe Class Project'

#Setup to use the database
try: 
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.times
    ftCollection = db.freeTimes
    btCollection = db.busyTimes

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)

#############################
#
#  Pages (routed from URLs)
#
#############################

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Entering index")
  if 'begin_date' not in flask.session:
    init_session_values()
  return render_template('index.html')

"""add_member also takes you to index.html, but it defines meetingID 
   in the session object before doing so. Then, I use jinja2 in 
   index.html to determine if this is a new meeting or if this is 
   an addition to an existing meeting."""
@app.route("/addMember")
def add_member():
    flask.session['meetingID'] = request.args.get('key')
    return render_template('index.html')

@app.route("/finalize")
def finalize():
    return render_template('finalize.html')

@app.route("/choose")
def choose():
    ## We'll need authorization to list calendars 
    ## I wanted to put what follows into a function, but had
    ## to pull it back here because the redirect has to be a
    ## 'return' 
    app.logger.debug("Checking credentials for Google calendar access")
    credentials = valid_credentials()
    if not credentials:
      app.logger.debug("Redirecting to authorization")
      return flask.redirect(flask.url_for('oauth2callback'))
    
    global gcal_service #Needs to be accessed by other functions
    gcal_service = get_gcal_service(credentials)
    app.logger.debug("Returned from get_gcal_service")
    flask.session['calendars'] = list_calendars(gcal_service)
    return render_template('index.html')

####
#
#  Google calendar authorization:
#      Returns us to the main /choose screen after inserting
#      the calendar_service object in the session state.  May
#      redirect to OAuth server first, and may take multiple
#      trips through the oauth2 callback function.
#
####

def valid_credentials():
    """
    Returns OAuth2 credentials if we have valid
    credentials in the session.  This is a 'truthy' value.
    Return None if we don't have credentials, or if they
    have expired or are otherwise invalid.  This is a 'falsy' value. 
    """
    if 'credentials' not in flask.session:
      return None

    credentials = client.OAuth2Credentials.from_json(
        flask.session['credentials'])

    if (credentials.invalid or
        credentials.access_token_expired):
      return None
    return credentials


def get_gcal_service(credentials):
  """
  We need a Google calendar 'service' object to obtain
  list of calendars, busy times, etc.  This requires
  authorization. If authorization is already in effect,
  we'll just return with the authorization. Otherwise,
  control flow will be interrupted by authorization, and we'll
  end up redirected back to /choose *without a service object*.
  Then the second call will succeed without additional authorization.
  """
  app.logger.debug("Entering get_gcal_service")
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('calendar', 'v3', http=http_auth)
  app.logger.debug("Returning service")
  return service

@app.route('/oauth2callback')
def oauth2callback():
  """
  The 'flow' has this one place to call back to.  We'll enter here
  more than once as steps in the flow are completed, and need to keep
  track of how far we've gotten. The first time we'll do the first
  step, the second time we'll skip the first step and do the second,
  and so on.
  """
  app.logger.debug("Entering oauth2callback")
  flow =  client.flow_from_clientsecrets(
      CLIENT_SECRET_FILE,
      scope= SCOPES,
      redirect_uri=flask.url_for('oauth2callback', _external=True))
  ## Note we are *not* redirecting above.  We are noting *where*
  ## we will redirect to, which is this function. 
  
  ## The *second* time we enter here, it's a callback 
  ## with 'code' set in the URL parameter.  If we don't
  ## see that, it must be the first time through, so we
  ## need to do step 1. 
  app.logger.debug("Got flow")
  print("Got flow")
  if 'code' not in flask.request.args:
    print("In if stagement")
    app.logger.debug("Code not in flask.request.args")
    auth_uri = flow.step1_get_authorize_url()
    print("Got auth_uri")
    return flask.redirect(auth_uri)
    ## This will redirect back here, but the second time through
    ## we'll have the 'code' parameter set
  else:
    ## It's the second time through ... we can tell because
    ## we got the 'code' argument in the URL.
    app.logger.debug("Code was in flask.request.args")
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    flask.session['credentials'] = credentials.to_json()
    ## Now I can build the service and execute the query,
    ## but for the moment I'll just log it and go back to
    ## the main screen
    app.logger.debug("Got credentials")
    return flask.redirect(flask.url_for('choose'))

#####
#
#  Option setting:  Buttons or forms that add some
#     information into session state.  Don't do the
#     computation here; use of the information might
#     depend on what other information we have.
#   Setting an option sends us back to the main display
#      page, where we may put the new information to use. 
#
#####

@app.route('/setrange', methods=['POST'])
def setrange():
    """
    User chose a date range with the bootstrap daterange
    widget.
    """
    # Can't store meetingID in session object because jinja uses it to see if you are a meeting proposer or a group member
    app.logger.debug("Entering setrange")  
    daterange = request.form.get('daterange')
    flask.session['daterange'] = daterange
    daterange_parts = daterange.split()
    flask.session['begin_date'] = interpret_date(daterange_parts[0])
    flask.session['end_date'] = interpret_date(daterange_parts[2])
    meetingID = str(random.random())
    meetingID = meetingID[2:] #get rid of the "0." in front of every number
    flask.session['createdID'] = meetingID
    record = { "type": "daterange", 
               "begin": flask.session['begin_date'],
               "end": flask.session['end_date'],
               "meetingID": meetingID
             }
    btCollection.insert(record)
    return flask.redirect(flask.url_for("choose"))

@app.route('/select_cal', methods=['POST'])
def get_cal():
    """Gets the selected checkboxes' values from getlist(), then sends
       the calendars to get_busy_times. Eventually redirects to index
       after the chain of method calls starting with get_busy_times 
       returns."""
    app.logger.debug("Entering get_cal")
    matches = []
    selected_calendars = request.form.getlist('calendar')
    all_user_calendars = flask.session['calendars']
    for cal in all_user_calendars:
        if cal['summary'] in selected_calendars:
            matches.append(cal)
    get_busy_times(matches)
    try:
        flask.flash("Your meeting identification number: {}".format(flask.session['createdID']))
        flask.flash("URL to add members to meeting: ix.cs.uoregon.edu:6789/addMember?key={}".format(flask.session['createdID']))
    except:
        flask.flash("You have added your availability to the meeting!")
    return flask.redirect(flask.url_for("index")) 

@app.route('/findMeeting', methods=['POST'])
def find_meeting():
    submittedID = request.form.get('meetingID')
    queryResult = btCollection.find({ "meetingID":submittedID }) 
    print("Got queryResult, about to get start and end dates")
    start = queryResult[0]['begin']
    end = queryResult[0]['end']
    print("Start: {}, End: {}".format(start,end))
    busyTimes = []
    if queryResult.count() != 0:
        for document in queryResult:
            if document['type'] == "busyTime":
                entry = (arrow.get(document['begin']).to('local'), arrow.get(document['end']).to('local'))
                busyTimes.append(entry) 
        print(busyTimes)
        print("Got busy times, sending to get_free_times")
        get_free_times(submittedID, busyTimes, start, end)
    else:
        flask.seesion['errorMessage'] = "Error: Invalid ID" 
    return render_template('finalize.html')

####
#
#   Initialize session variables 
#
####

def init_session_values():
    """
    Start with some reasonable defaults for date and time ranges.
    Note this must be run in app context ... can't call from main. 
    """
    # Default date span = tomorrow to 1 week from now
    now = arrow.now('local')
    tomorrow = now.replace(days=+1)
    nextweek = now.replace(days=+7)
    flask.session["begin_date"] = tomorrow.floor('day').isoformat()
    flask.session["end_date"] = nextweek.ceil('day').isoformat()
    flask.session["daterange"] = "{} - {}".format(
        tomorrow.format("MM/DD/YYYY"),
        nextweek.format("MM/DD/YYYY"))
    # Default time span each day, 8 to 5
    flask.session["begin_time"] = interpret_time("9am")
    flask.session["end_time"] = interpret_time("5pm")

def interpret_time( text ):
    """
    Read time in a human-compatible format and
    interpret as ISO format with local timezone.
    May throw exception if time can't be interpreted. In that
    case it will also flash a message explaining accepted formats.
    """
    app.logger.debug("Decoding time '{}'".format(text))
    time_formats = ["ha", "h:mma",  "h:mm a", "H:mm"]
    try: 
        as_arrow = arrow.get(text, time_formats).replace(tzinfo=tz.tzlocal())
        app.logger.debug("Succeeded interpreting time")
    except:
        app.logger.debug("Failed to interpret time")
        flask.flash("Time '{}' didn't match accepted formats 13:30 or 1:30pm"
              .format(text))
        raise
    return as_arrow.isoformat()

def interpret_date( text ):
    """
    Convert text of date to ISO format used internally,
    with the local time zone.
    """
    try:
      as_arrow = arrow.get(text, "MM/DD/YYYY").replace(
          tzinfo=tz.tzlocal())
    except:
        flask.flash("Date '{}' didn't fit expected format 12/31/2001")
        raise
    return as_arrow.isoformat()

def next_day(isotext):
    """
    ISO date + 1 day (used in query to Google calendar)
    """
    as_arrow = arrow.get(isotext)
    return as_arrow.replace(days=+1).isoformat()

####
#
#  Functions (NOT pages) that return some information
#
####
  
def list_calendars(service):
    """
    Given a google 'service' object, return a list of
    calendars.  Each calendar is represented by a dict, so that
    it can be stored in the session object and converted to
    json for cookies. The returned list is sorted to have
    the primary calendar first, and selected (that is, displayed in
    Google Calendars web app) calendars before unselected calendars.
    """
    app.logger.debug("Entering list_calendars")  
    calendar_list = service.calendarList().list().execute()["items"]
    result = [ ]
    for cal in calendar_list:
        kind = cal["kind"]
        id = cal["id"]
        if "description" in cal: 
            desc = cal["description"]
        else:
            desc = "(no description)"
        summary = cal["summary"]
        # Optional binary attributes with False as default
        selected = ("selected" in cal) and cal["selected"]
        primary = ("primary" in cal) and cal["primary"]
        
        result.append(
          { "kind": kind,
            "id": id,
            "summary": summary,
            "selected": selected,
            "primary": primary
            })
    return sorted(result, key=cal_sort_key)


def cal_sort_key( cal ):
    """
    Sort key for the list of calendars:  primary calendar first,
    then other selected calendars, then unselected calendars.
    (" " sorts before "X", and tuples are compared piecewise)
    """
    if cal["selected"]:
       selected_key = " "
    else:
       selected_key = "X"
    if cal["primary"]:
       primary_key = " "
    else:
       primary_key = "X"
    return (primary_key, selected_key, cal["summary"])

def get_busy_times( calendars ):
    app.logger.debug("Entering get_busy_times")
    busyTimes = []
    userType = None
    try:
        result = btCollection.find({ "type":"daterange", "meetingID":flask.session['createdID'] })[0]
        userType = "Proposer"
    except:
        result = btCollection.find({ "type":"daterange", "meetingID":flask.session['meetingID'] })[0]
        userType = "Member"
    begin_date = result['begin']
    end_date = result['end']
    if begin_date == end_date:                          #When the user is looking for a meeting time during 1 day:
        end_date = arrow.get(end_date).replace(days=+1).isoformat() #Add a day to the range so the query can get events for a full 24 hours
    for cal in calendars:
        freebusy_query = {              # The query to google calendar
        "timeMin" : begin_date,
        "timeMax" : end_date,
        "items" :[{ "id" : cal['id'] }]
        }
        result = gcal_service.freebusy().query(body=freebusy_query).execute() # results of the query: all busy times for that date range
        resultTimes = result['calendars'][cal['id']]['busy'] # Extract busy times from response
        if userType == "Proposer":
            ID = flask.session['createdID']
        else:
            ID = flask.session['meetingID']
        if resultTimes:#If the list is not empty
            for startEndPair in resultTimes:
                start = startEndPair['start']
                end = startEndPair['end']
                document = {
                "type": "busyTime",
                "begin": start,
                "end": end,
                "meetingID": ID
                }
                print(document)
                btCollection.insert(document)
    
def get_free_times(ID, busyTimes, startTime, endTime):
    app.logger.debug("Entering get_free_times")
    freeTimes = []
    startTime = arrow.get(startTime)
    endTime = arrow.get(endTime)
    print("In get_free_times, calling addNights")
    allBusyTimes = addNights(busyTimes, startTime, endTime) # add busy times for each day 9pm - 5am
    print("Successful, calling sortedTimes")
    print(allBusyTimes)
    sortedTimes = sorted(allBusyTimes, key=lambda times: times[0]) #put them in chronological order
    print("Successfull, calling fix_overlaps")
    unionizedTimes = fix_overlaps(sortedTimes) #get rid of overlapping times
    print("Starting calculations")
    for i in range(len(unionizedTimes)):
        if i == 0:
            if startTime < startTime.replace(hour=9, minute=0):#If default starttime is before 9am that day
                startTime = startTime.replace(hour=9, minute=0)#Change the starttime to 9am that day.
            if unionizedTimes[i][0] > unionizedTimes[i][0].replace(hour=17, minute=0):#If the first event's end time is after 5pm
                correctedTime = unionizedTimes[i][0].replace(hour=17, minute=0)#Change end time to 5pm
                beforeFirstEvent = (startTime, correctedTime)
            else:
                beforeFirstEvent = (startTime, unionizedTimes[i][0])
            freeTimes.append(beforeFirstEvent)
        elif (i > 0) and (i < (len(unionizedTimes)-1)):#If its the first or last time in the loop
            if unionizedTimes[i-1][1].hour == 9:#if the starttime is 9am
                withOrWithoutAddedTime = unionizedTimes[i-1][1] #leave as is
            else:#If not, this means the start time is the end of a busy time. 
                withOrWithoutAddedTime = unionizedTimes[i-1][1].replace(minutes=+15)#So we need to add 15 minutes to the start time
            freeTime = (withOrWithoutAddedTime, unionizedTimes[i][0])
            freeTimes.append(freeTime)
        else:
            endTime = endTime.replace(hour=17, minute=0)#endtime will by default be midnight, so we change it to 5pm
            if unionizedTimes[i-1][1] < unionizedTimes[i-1][1].replace(hour=9, minute=0):#If the end time of the last busy time ends before 9am
                correctedTime = unionizedTime[i-1][1].replace(hour=9, minute=0)#Change the end time to 9pm
                afterLastEvent = (correctedTime, endTime)
            else:#The end time of the last busy time is after 9am
                afterLastEvent = (unionizedTimes[i-1][1], endTime)#Therefore we do not need to add time.
            freeTimes.append(afterLastEvent)
    print("Calculations successful, calling display_free_times")
    display_free_times(freeTimes)
    print("returning")
    return freeTimes

def addNights(times, startTime, endTime):
    app.logger.debug("Entering addNights")
    print("About to get days in range")
    days = arrow.Arrow.span_range('day', startTime, endTime)#Get a list of days, each with a start and end time
    print("Got days, iterating:")
    for day in days:
        #Create busy times from 5pm of one day to 9am of the next, making nights unavailable for free times
        busyNightTime = (day[0].replace(hour=17, minute=0), day[1].replace(days=+1, hour=9, minute=0, second=0, microsecond=0))
        times.append(busyNightTime)
        print("Successfully inserted times")
    return times 

def fix_overlaps(times):
    app.logger.debug("Entering fix_overlaps")
    for i in range(len(times)-1):
        if i < (len(times)-1):
            if times[i][1] > times[i+1][0]:#if the ending time of the current is greater than the starting time of the next
                if times[i][1] < times[i+1][1]:#if the ending time of the current is less than the ending time of the next
                    newTuple = (times[i][0],times[i+1][1])#Combine the start of the current and the end of the next
                else:
                    newTuple = times[i]#The next event is within the starting and ending time of the current
                del times[i+1]
                times[i] = newTuple
                i = i-1			#Because len(times) decreases by one after deleting times[i+1]
    return times

def display_free_times(times):
    for time in times:
        start = time[0].format('MM/DD/YYYY h:mm a')
        end = time[1].format('MM/DD/YYYY h:mm a')
        try:
            flask.flash("Free Time: {} - {}".format(start,end)) #Story in flask flash object. Will store in mongo in Project 8
        except RuntimeError:
            continue

#################
#
# Functions used within the templates
#
#################

@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
    try: 
        normal = arrow.get( date )
        return normal.format("ddd MM/DD/YYYY")
    except:
        return "(bad date)"

@app.template_filter( 'fmttime' )
def format_arrow_time( time ):
    try:
        normal = arrow.get( time )
        return normal.format("HH:mm")
    except:
        return "(bad time)"
    
#############


if __name__ == "__main__":
  # App is created above so that it will
  # exist whether this is 'main' or not
  # (e.g., if we are running in a CGI script)

  app.secret_key = str(uuid.uuid4())  
  app.debug=CONFIG.DEBUG
  app.logger.setLevel(logging.DEBUG)
  # We run on localhost only if debugging,
  # otherwise accessible to world
  if CONFIG.DEBUG:
    # Reachable only from the same computer
    app.run(port=CONFIG.PORT)
  else:
    # Reachable from anywhere 
    app.run(port=CONFIG.PORT,host="0.0.0.0")
