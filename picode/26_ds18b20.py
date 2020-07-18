#!/usr/bin/env python3
#----------------------------------------------------------------
#	Note:
#		ds18b20's data pin must be connected to pin7.
#		replace the 28-XXXXXXXXX as yours.
#----------------------------------------------------------------
import os
import time
from google.cloud import pubsub_v1
import json
from google.auth import jwt
from datetime import datetime

# TODO(developer)
project_id = "thetechrambler-177118"
topic_id = "office-temp"

#publisher = pubsub_v1.PublisherClient()
#topic_path = publisher.topic_path(project_id, topic_id)

ds18b20 = ''

service_account_info = json.load(open("/home/pi/Documents/SunFounder_SensorKit_for_RPi2/Python/sunfounder_probe.json"))
print("Svc Account:")
print(service_account_info)

#service_account_info = json.load(open("sunfounder_probe.json"))
audience = "https://pubsub.googleapis.com/google.pubsub.v1.Subscriber"

credentials = jwt.Credentials.from_service_account_info(
    service_account_info, audience=audience
)
#print("Creds: ")
#print(credentials)

#publisher = pubsub_v1.PublisherClient()
#create a client with a json service account token
#publisher.from_service_account_json("/home/pi/Documents/SunFounder_SensorKit_for_RPi2/Python/sunfounder_probe.json")
#print("publisher: " + publisher)

#topic_path = publisher.topic_path(project_id, topic_id)

# The same for the publisher, except that the "audience" claim needs to be adjusted
publisher_audience = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
credentials_pub = credentials.with_claims(audience=publisher_audience)
publisher = pubsub_v1.PublisherClient(credentials=credentials_pub)

topic_path = publisher.topic_path(project_id, topic_id)

# datetime object containing current date and time
now = datetime.now()
# dd/mm/YY H:M:S
dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

def setup():
	global ds18b20
	for i in os.listdir('/sys/bus/w1/devices'):
		if i != 'w1_bus_master1':
			ds18b20 = '28-00000a691f27'

def publish():
	# datetime object containing current date and time
	now = datetime.now()
	# dd/mm/YY H:M:S
	dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

	data = u"{}:{}".format(read(), dt_string)
	# Data must be a bytestring
	data = data.encode("utf-8")
    	# Add two attributes, origin and username, to the message
    	future = publisher.publish(
        	topic_path, data, origin="Barrys office", username="gcp"
    	)
    	print(future.result())

def read():
#	global ds18b20
	location = '/sys/bus/w1/devices/' + ds18b20 + '/w1_slave'
	tfile = open(location)
	text = tfile.read()
	tfile.close()
	secondline = text.split("\n")[1]
	temperaturedata = secondline.split(" ")[9]
	temperature = float(temperaturedata[2:])
	temperature = temperature / 1000
	return temperature
	
def loop():
	while True:
		# datetime object containing current date and time
        	now = datetime.now()
        	# dd/mm/YY H:M:S
        	dt_minute = now.strftime("%M")
		dt_second = now.strftime("%S")
		
		print(now.strftime("%Y-%m-%d %H:%M:%S"))

		time.sleep(1)
		if  int(dt_second)==0 and int(dt_minute)%5==0:
			if read() != None:
				print ("Current temperature : %0.3f C" % read())
				publish()

def destroy():
	pass

if __name__ == '__main__':
	try:
		setup()
		loop()
	except KeyboardInterrupt:
		destroy()

