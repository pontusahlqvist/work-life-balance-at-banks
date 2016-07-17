import numpy as np
import csv

percentages_cash = []
percentages_cred = []

fpaths = ['trip_fare_1.csv']
for fpath in fpaths:
	print 'Opening to Read file %s'%fpath
	f = open(fpath,'r')
	reader = csv.reader(f)
	header = next(reader)

	for row in reader:
		try:
			fare = float(row[10])
			tip  = float(row[8])
		except:
			continue

		if fare <= tip or fare == 0:
			continue

		payment_type = row[4]
		if payment_type == 'CSH':
			percentages_cash.append(tip/fare)
		elif payment_type == 'CRD':
			percentages_cred.append(tip/fare)

print 'CASH: Tip average is %f with a standard deviation of %f. The max is %f and the min is %f'%(np.average(percentages_cash), np.std(percentages_cash), max(percentages_cash), min(percentages_cash))
print 'CREDIT CARD: Tip average is %f with a standard deviation of %f. The max is %f and the min id %f.'%(np.average(percentages_cred), np.std(percentages_cred), max(percentages_cred), min(percentages_cred))


