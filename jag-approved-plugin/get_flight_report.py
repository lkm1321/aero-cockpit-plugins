from __future__ import print_function

import os
import argparse
import time

import numpy as np

import cProfile
import re

from pyulog import ULog

def main():

	parser = argparse.ArgumentParser(description="Get flight time and battery voltages")
	parser.add_argument('logs_path', default='/var/lib/mavlink_router')
	parser.add_argument('num_recent', default="1", type=int, nargs='?')

	args = parser.parse_args()

	# ulog_list = os.listdir(args.logs_path)

	# for ulog_file in ulog_list:
	
	if not os.path.isdir(args.logs_path):
		get_flight_report(args.logs_path)
	else: 


		ulog_file_list = os.listdir(args.logs_path)
		# Filename is of the form <seqnum>-YYYY-MM-DD_HH-MM-SS.ulg. Sort by seqnum
		ulog_file_list.sort(key = lambda filename: int( filename.split('-')[0] )) 
		print('Displaying {0} most recent logs.\n\n'.format(str(args.num_recent)))
		num_recent_san = args.num_recent if args.num_recent is not None else 5
		num_files = min(len(ulog_file_list), int(num_recent_san)) 

		# Start from current. 
		cur_file_idx = -1

		while num_files > 0:
			ulog_file = ulog_file_list[cur_file_idx]

			# Decrement file count iff it's a valid log. 
			if get_flight_report(args.logs_path + '/'+ ulog_file) is True:
				num_files = num_files - 1

		#	print(num_files)
			cur_file_idx = cur_file_idx - 1

def test_main(): 
	ulog_file_list = os.listdir("../../logs")
	# Filename is of the form <seqnum>-YYYY-MM-DD_HH-MM-SS.ulg. Sort by seqnum
	ulog_file_list.sort(key = lambda filename: int( filename.split('-')[0] )) 
	print('Displaying {0} most recent logs.\n\n'.format(str(5)))
	#num_recent_san = args.num_recent if args.num_recent is not None else 5
	#num_files = min(len(ulog_file_list), int(num_recent_san)) 
	num_files = 5
	# Start from current. 
	cur_file_idx = -1

	while num_files > 0:
		ulog_file = ulog_file_list[cur_file_idx]

		# Decrement file count iff it's a valid log. 
		if get_flight_report('../../logs/'+ ulog_file) is True:
			num_files = num_files - 1

	#	print(num_files)
		cur_file_idx = cur_file_idx - 1


def get_flight_report(ulog_file):

	print(ulog_file)
	try:
		
		ulog = ULog(ulog_file, ['vehicle_status', 'battery_status', 'vehicle_gps_position'])
		vehicle_status = ulog.get_dataset('vehicle_status')
		battery_status = ulog.get_dataset('battery_status')
		utc_avail = False		
		# Processing arming data. 

		armed_data = vehicle_status.data['arming_state'] # 1 is standby, 2 is armed. 
		armed_tstamp = vehicle_status.data['timestamp']  # in us. 

		was_armed = np.any(armed_data == 2)

		if not was_armed:
			del ulog
			return False

		try: 
			gps_position = ulog.get_dataset('vehicle_gps_position')
			start_time = time.localtime(gps_position.data['time_utc_usec'][0]/1E6) # in us since epoch
			# boot_time = time.localtime(gps_position.data['timestamp'][0]/1E6) # in us since FC boot
			utc_avail = True
		except:
			utc_avail = False


		batt_v_start = battery_status.data['voltage_filtered_v'][0]
		batt_v_end = battery_status.data['voltage_filtered_v'][-1]
		# batt_v_tsamp = battery_status.data['timestamp'] # in us. 

		arm_disarm_idx = np.where(armed_data[:-1] != armed_data[1:]) # Find where arming state changes by comparing to neighbor. 
		arm_disarm_events = armed_data[arm_disarm_idx]
		arm_disarm_events_tstamp = armed_tstamp[arm_disarm_idx]
		arm_disarm_durations = ( arm_disarm_events_tstamp[1::2] - arm_disarm_events_tstamp[0::2] ) / 1E6 # Assume every second event is arming. Can't be armed on boot!
		arm_disarm_total_time = arm_disarm_durations.sum()
		arm_min, arm_sec = divmod(arm_disarm_total_time, 60)
		arm_min = int(arm_min) # because it's an integer. 

		if utc_avail:
			print('System powered on {0}'.format(time.asctime(start_time)))
		else:
			print('No GPS. No UTC time')
		print('Log file name: {0}'.format(ulog_file))
		print('Arm duration: {0} min {1} sec'.format( str(arm_min), str(arm_sec) ))
		print('Start voltage: {0}V, End voltage: {1}V'.format(str(batt_v_start), str(batt_v_end)))
		print('\n\n')
		del ulog
		return True

	except IndexError:
	#	print('Empty or invalid file')
		return False
	except Exception as e: 
	# 	print(str(e))
		return False 

# test_main()
# cProfile.run('re.compile("test_main")')
 
main()