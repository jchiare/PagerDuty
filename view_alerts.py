#!/usr/bin/python
# Summary: Finds all the 'triggered' status alerts within an incident, and mass resolves them

import requests
import sys
import json
import time

# Get the following information from the user:
# authentication token, incident ID, and "from" email address
auth_token = raw_input("Enter full REST API v2 key: ")
incident_id = raw_input("Enter incident ID please: ")
from_email = raw_input("Enter 'from' email address: (has to match an existing users' login) ")
limit_amount = int(raw_input("Enter the limit parameter (how many alerts to resolve per API call): "))

# Whip up the HTTPS request session
request = requests.Session()

# Add the request headers, mostly from the user input
request.headers = {
	'Authorization': 'Token token={0}'.format(auth_token),
	'Accept': 'application/vnd.pagerduty+json;version=2',
    'Content-Type': 'application/json',
    'From': '{0}'.format(from_email)
}

triggered_alerts_id = []
resolved_alerts_amount = 0
alerts_searched_amount = 0


# See why this is necessary: https://pagerduty.atlassian.net/browse/NAR-214
def findAndAppendTriggeredAlerts(alerts):
    for key in alerts:
        if key['status'] == 'triggered':
            triggered_alerts_id.append(key['id'].encode('utf8'))

# The API expects each Alert object to be a specific format
def createFormattedAlertObject(id):
    formatted_alert = {'id': '','type': 'alert_reference','status': 'resolved'}
    formatted_alert['id'] = id
    return formatted_alert

# Take the triggered alerts, run the second API call, and mass resolve them
def resolveTriggeredAlerts():
    global resolved_alerts_amount
    resolve_these_alerts = []
    length_of_triggered_alerts = len(triggered_alerts_id)
        
    for number in range(length_of_triggered_alerts):
        try:
            resolve_these_alerts.append(createFormattedAlertObject(triggered_alerts_id.pop()))
        except Exception as ex:
            print 'Failed on adding open alert to array of IDs to be resolved'
    
    try:
        DATA = json.dumps({"alerts":resolve_these_alerts})
        URL = 'https://api.pagerduty.com/incidents/{0}/alerts'.format(incident_id)
        response = request.put(URL,data=DATA)
        resolved_alerts_amount += len(resolve_these_alerts)      
        print 'Resolved {0} open alerts, out of attempted {1}, for incident #{2}'.format(resolved_alerts_amount,alerts_searched_amount ,incident_id)
    except Exception as ex:
        print str(ex)    

# Start here -- get the alerts from the incident, this is where the first API call is
while True:

    try:        
        URL = 'https://api.pagerduty.com/incidents/{0}/alerts?limit={1}&total=true'.format(incident_id,limit_amount)
        data = request.get(URL).json() 
        findAndAppendTriggeredAlerts(data['alerts'])
        
        alerts_searched_amount += limit_amount
        resolveTriggeredAlerts()

        if (alerts_searched_amount >= data['total']): # ends while loop if there are no more alerts within the incident
            break

    except Exception as ex:
        print ex
        break


print "Done"