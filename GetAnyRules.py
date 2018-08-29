import urllib2 #used for http requests
import xml.etree.ElementTree as ET 
import sys
import os
import time
import datetime
from multiprocessing.dummy import Pool as ThreadPool

ip_address = "x.x.x.x"
apiKey = "XXXXX"
startTime = time.time()
filePath = os.path.join('C:/', 'TestMultiLog' + datetime.datetime.now().strftime("_%m-%d-%y_%S") + '.txt')
logString =  "*****GetRules Script started*****"

def getTime(): #Gets the current time and formats it
	time = datetime.datetime.now().strftime("%m-%d-%y %H:%M:%S")
	return time

def setLog(logString): #Logs to a file and appends newlines
	with open(filePath, 'a') as logFile:
		logFile.write(getTime() + " : " + logString + '\n')

def GetDeviceGroups(): #Gets the Device Groups from Panorama
	try:
		cmd = '&cmd=<show><devicegroups/></show>'
		url = 'https://'+ ip_address +'/api/?type=op'+ apiKey + cmd
		response = urllib2.urlopen(url) #Basically a curl
		html = response.read() #Read the curl and assign it to string variable
		logString = "HTML accessed : " + url
		setLog(logString)
	except:
		logString = "Invalid credentials or IP address. Check username and password"
		setLog(logString)
		#sys.exit(1) #Stop the script

	
	contents = ET.fromstring(html) #import the xml through a string
	devicegroups = []
	if contents.attrib == {'status': 'success'}:
		 for item in contents.findall('./result/devicegroups/entry'):
				#print item.attrib['name']
				devicegroups.append(item.attrib['name'])
				logString = item.attrib['name']
				logString = "Added " + logString + " to Device Group List"
				setLog(logString)
				
	else:
		print "API call failed. Check credentials"
		logString = "API call failed. Check credentials"
		setLog(logString)
		devicegroups = ["BAD"]
		#sys.exit(1) #Stop the script

	return devicegroups
	
def GetRules(device): #Builds a rules list, then searches through them for source/destination ANYs
	logString = "Get Rules Method is running for " + device
	setLog(logString)

	#for device in devicegroups:
	cmd = "&xpath=/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='"+ device +"']/post-rulebase/security"
	url = 'https://'+ ip_address +'/api/?type=config&action=get'+ apiKey + cmd
	#Remove spaces from URL string. URLLIB2 is too stupid for them
	if " " in url:
			url = url.replace(" ", "+")
			logString = "URL corrected : " + url
			setLog(logString)
			
	try:
		response = urllib2.urlopen(url) #Basically a curl
		#print url
		html = response.read() #Read the curl and assign it to string variable
		contents = ET.fromstring(html)
		
	except:
		logString = "Failed to reach " + url
		setLog(logString)
	
	rules = []
		
	for item in contents.findall('./result/security/rules/entry'):
			rules.append(item.attrib['name'])
			#logString = "Adding " + item.attrib['name'] + " to Rules List"
			#setLog(logString)					
	
	for rule in rules:
		logString = "Parsing the XML for Device Group: " + device + " and Rule: " + rule
		setLog(logString)
		#Check if rule is disabled
		for item in contents.findall(".//*[@name='" + rule + "']/disabled"):
			IsDisabled = item.text
			if ("no" in IsDisabled):
				#Check if rule is allow or deny because we probably dont care about Deny any/anys
				for item in contents.findall(".//*[@name='" + rule + "']/action"):
					IsAllow = item.text
					if ("allow" in IsAllow):
						#Find the source address(es)
						for item in contents.findall(".//*[@name='" + rule + "']/source/member"):
							source = item.text
							if ("any" in source): #Check for anys in the source
								for item in contents.findall(".//*[@name='" + rule + "']/destination/member"):
									destination = item.text
									#Find the destination address(es)
									if ("any" in destination): #Check for anys in the destination
										print "Rule " + rule + " in Device Group : " + device + " contains an ANY/ANY rule" 
										logString = "Rule " + rule + " in Device Group : " + device + " contains an ANY/ANY rule" 
										setLog(logString)
		
setLog(logString)

devicegroupsList = GetDeviceGroups()
thread = 2 #Adjust this to the number of cores you have. x2 if you have hyperthreading

#Use threading to loop through the GetRules method quicker
if __name__ == '__main__':
	pool = ThreadPool(thread)
	#pool = Pool(4)
	pool.map(GetRules, devicegroupsList)
	pool.close() 
	pool.join() 

#Used for testing the thread count. If your PC can handle more threads then do so
print "It took " + str(time.time()-startTime) + " seconds to run this script. Thread = " + str(thread)
logString = "It took " + str(time.time()-startTime) + "seconds to run this script. Thread = " + str(thread)
setLog(logString)
logString = "*****Script complete*****"
setLog(logString)
