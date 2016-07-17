import matplotlib.pyplot as plt
import numpy as np
import csv
import time
import sys
import datetime
from sklearn.cluster import KMeans

maxPickups = 1000000000

##################################################################
#####################  HELPER FUNCTIONS  #########################
##################################################################

# This function converts seconds into the nearest hour:minute format
def toTime(seconds):
	hours   = int(seconds)/3600
	minutes = (int(seconds)-3600*hours)/60
	return '%02d:%02d'%(hours,minutes)

# This function converts degrees into radians
def toRad(deg):
	return deg*np.pi/180.0

# This function computes the distance between two lat-longs
def distFromGPS(latlong1, latlong2):
	R = 6371000 #meters
	dLat = toRad(latlong2[0] - latlong1[0])
	dLon = toRad(latlong2[1] - latlong1[1])
	lat1 = toRad(latlong1[0])
	lat2 = toRad(latlong2[0])
	a = np.sin(dLat/2)* np.sin(dLat/2) + np.sin(dLon/2) * np.sin(dLon/2) * np.cos(lat1) * np.cos(lat2); 
	c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a)); 
	d = R * c;
	return d

# This function identifies which hotspot (bank) a given GPS coordinate is nearest (if it's sufficiently near any of them)
def identifyHotspot(latlong, locations):
	#tells us how far off of the sweet spot GPS coordinates to even look. By having these hard cutoffs prior to doing a distance 
	#computation, we can save a lot of unnecessary comparisons between e.g. queens and the Goldman Sachs office. 
	longdelta = 0.0012
	latdelta  = 0.001

	nearHotspot = False
	for loc in locations:
		if latlong[0] > loc[0]-latdelta and latlong[0] < loc[0]+latdelta and latlong[1] > loc[1]-longdelta and latlong[1] < loc[1]+longdelta:
			nearHotspot = True
			break
	if not nearHotspot:
		return -1 

	#if we make it here, the point is sufficiently near one of the headquarters that a proper distance calculation is warranted
	bestInd = -1
	minDistance = 50 #cutoff distance from office in meters
	for ind,loc in enumerate(locations):
		dist = distFromGPS(latlong, loc)
		if dist < minDistance:
			minDistance = dist
			bestInd = ind
	return bestInd	

# This function converts time values into a 2D space (cos,sin) to allow for clustering and averaging
def timeToR2(timeValues):
	return [[np.cos(t*np.pi/(12*3600)), np.sin(t*np.pi/(12*3600))] for t in timeValues] #t is in seconds. Set midnight as theta = 0

# This function takes 2D values and reverses them back to time values
def R2ToTime(R2Value):
	return (np.arctan2(R2Value[1],R2Value[0])*(12*3600)/np.pi)%(24*3600) #ensure that we get a positive number back

def periodicAverage(tValues):
	R2Average = np.average(timeToR2(tValues), axis=0)
	return R2ToTime(R2Average) 

def periodicStd(tValues):
	avgValue = periodicAverage(tValues)
	differences = [min((t-avgValue)%(24*3600),(avgValue-t)%(24*3600)) for t in tValues]
	return (np.average([d**2 for d in differences]))**0.5

##################################################################
######################  MAIN EXECUTION  ##########################
##################################################################

#locations of a few major investmentbanks
bankNames = ['Bank of America Merril Lynch', 'Barclays Capital', 'Citi', 'Credit Suisse', 'Deutsche Bank', 'Goldman Sachs', 'J.P. Morgan', 'Morgan Stanley']
bankLocations  = [[40.755603, -73.984931],[40.760542, -73.982903], [40.759119, -73.971885], [40.741791, -73.986962], [40.706205, -74.008536], [40.714854, -74.014497], [40.755882, -73.975584], [40.760056, -73.985418]]
#pickup times of pickups/dropoffs by bank
pickupTimesByBank  = [[] for i in range(len(bankNames))]
employeesLeavingByBank = [[] for i in range(len(bankNames))]

#read data from files
fpaths = ['trip_data_1.csv', 'trip_data_2.csv', 'trip_data_3.csv', 'trip_data_4.csv', 'trip_data_5.csv', 'trip_data_6.csv', 'trip_data_7.csv', 'trip_data_8.csv', 'trip_data_9.csv', 'trip_data_10.csv', 'trip_data_11.csv', 'trip_data_12.csv']
for fpath in fpaths:
	print 'Opening to Read file %s'%fpath
	f = open(fpath,'r')
	reader = csv.reader(f)
	header = next(reader)

	ind = 0
	rowCount = 0
	for row in reader:
		rowCount += 1
		if rowCount % 100000 == 0:
			print "Total rows examined = %d"%(rowCount)
		if ind == maxPickups:
			break

		try:
			newPickupLong  = float(row[10].strip())
			newPickupLat   = float(row[11].strip())
			pt = datetime.datetime.strptime(row[5].strip(), '%Y-%m-%d %H:%M:%S')	
		except:
			print "Either couldn't convert pickup lat/long to float: %s,%s, or couldn't convert date %s to datetime"%(row[10].strip(),row[11].strip(), pickupTime)
			continue #skip this ride and continue to the next one

		#figure out which bank this pickup corresponds to (if any) and log the time to that bank.
		bankIndex = identifyHotspot([newPickupLat, newPickupLong], bankLocations)
		if not bankIndex == -1: 
			pickupTimesByBank[bankIndex].append(pt.hour*3600 + pt.minute*60 + pt.second)
			ind += 1
			continue #in doing this we're saving computation time at the expense of throwing away potential bank-to-bank trips

	# Most of the pickup times seem to exhibit bimodal distributions, presumably since the rides don't all correspond to people leaving work. So, we perform
	# a simple k-means with k=2 to approximate the people leaving after their workday

	clusterer = KMeans(n_clusters=2)
	for ind,bank in enumerate(bankNames):
		#In order to properly cluster timevalues, we must take into consideration that they are periodic. We first transform 
		#into 2D and then perform a kMeans clustering there.
		c_labels = clusterer.fit_predict(timeToR2(pickupTimesByBank[ind])) #necessary for kMeans to work with periodic variables
		timesCluster1 = [pickupTimesByBank[ind][i] for i in np.where(np.array(c_labels)==0)[0]]
		timesCluster2 = [pickupTimesByBank[ind][i] for i in np.where(np.array(c_labels)==1)[0]]
		if periodicAverage(timesCluster1) > periodicAverage(timesCluster2):
			employeesLeavingByBank[ind] += timesCluster1
		else:
			employeesLeavingByBank[ind] += timesCluster2

for ind,bank in enumerate(bankNames):
	plt.clf()
	print 'employeesLeavingByBank[%d] has length %d'%(ind,len(employeesLeavingByBank[ind]))
	plt.hist(employeesLeavingByBank[ind], 100)
	plt.title('Pickup at %s'%(bank))
	mean = toTime(periodicAverage(employeesLeavingByBank[ind]))
	stdSeconds = periodicStd(employeesLeavingByBank[ind])
	std = toTime(stdSeconds)
	plt.text(plt.xlim()[1]*0.35,plt.ylim()[1]*0.9, r'$\mu = %s, \sigma = %s$'%(mean,std))
	plt.savefig('%s.jpg'%bank)
#	plt.show()

f.close()






