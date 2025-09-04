'''
switch to power screen (battery, volts, watts)
'''

'''
	Set enviroment var
'''
import os
if 'BLINKA_MCP2221' not in os.environ:
	os.environ['BLINKA_MCP2221'] = '1'

import mcp, psutil, time, pystray, threading, s_probe
from PIL import Image

n=0
mcp_running = True
laptop = False

def diskio():
	disks = psutil.disk_io_counters(perdisk=True)

	rb = disks[f'PhysicalDrive{n}'].read_bytes
	wb = disks[f'PhysicalDrive{n}'].write_bytes
	rt = disks[f'PhysicalDrive{n}'].read_time
	wt = disks[f'PhysicalDrive{n}'].write_time

	time.sleep(1)

	disks = psutil.disk_io_counters(perdisk=True)

	read = round((disks[f'PhysicalDrive{n}'].read_bytes - rb) / 1000000, 2)
	writ = round((disks[f'PhysicalDrive{n}'].write_bytes - wb) / 1000000, 2)
	rt = disks[f'PhysicalDrive{n}'].read_time - rt
	wt = disks[f'PhysicalDrive{n}'].write_time - wt

	#print(f'\33[2K\r{read}MB {writ}MB {rt}ms {wt}ms', end='')
	return [read, writ, rt, wt]


def netio(prev):
	#global netb
	#netb = psutil.net_io_counters(pernic=True)['Ethernet']
	#time.sleep(1)
	net = psutil.net_io_counters(pernic=True)['Ethernet']

	# / 125000 for Mb, / 1_000_000
	nettx = round(((net.bytes_sent - prev.bytes_sent) / 125_000), 3)
	netrx = round(((net.bytes_recv - prev.bytes_recv) / 125_000), 3)

	return [netrx, nettx]

	#if (net.bytes_sent - prev.bytes_sent) * 8 > 1_000_000:
	#	print(f'\r{netrx}Mb/s Down {nettx}Mb/s Up', end='')
	#else:
	#print(f'\r{netrx}Kb/s Down {nettx}Kb/s Up', end='')	


def bat():
	if laptop:
		return f'{psutil.sensors_battery().percent}%'
	else:
		return ''
	

def on_exit(icon):
	global mcp_running
	mcp_running = False
	mcp_t.join()
	m.clear()
	icon.stop()


def on_click(icon, item):
	global mcp_running, mcp_t
	mcp_running = False
	
	mcp_t.join()
	
	if item.text == 'Info':
		mcp_t = threading.Thread(target=info_screen)
	elif item.text == 'Battery':
		mcp_t = threading.Thread(target=bat_screen)
	
	if not mcp_t.is_alive():
		mcp_running = True
		mcp_t.start()


'''
	Displays CPU, RAM, disk and net info on oled
'''
def info_screen():
	vline = 58
	while mcp_running:
		#st = time.perf_counter()
		netb = psutil.net_io_counters(pernic=True)['Ethernet']
		m.display.fill(0)
		m.cpu_bar(psutil.cpu_percent(interval=0))
		m.ram(psutil.virtual_memory().percent)
		m.display.vline(vline, 0, m.h, 1)
		m.disk(diskio())
		m.display.hline(vline, m.h//2, m.w, 1)
		m.net(netio(netb))
		#print(time.perf_counter() - st, end='\r')
		# 0.2s
		m.display.show()
		

'''
	Displays battery info on oled
'''
def bat_screen():
	probe = s_probe.sProbe()
	while mcp_running:
		info = {'percent': probe.win32bat['EstimatedChargeRemaining'], 'volts': probe.voltage, 'amps': probe.amps, 'watts': probe.watts,
		  'cap': probe.msbatt['BatteryFullChargedCapacity']['FullChargedCapacity'], 'health': probe.get_health()}
		m.battery(info)
		time.sleep(1)


def vid(folder):
	import pathlib
	x=0
	for f in pathlib.Path(folder).iterdir():
		if mcp_running:
			st = time.perf_counter()
			m.show_image(f'{f}')
			print(round(1/(time.perf_counter() - st), 2), end='\r')
			#time.sleep(0.1)
		#print(f, f'{x:04d}')
		#x+=1


if __name__ == '__main__':
	if psutil.sensors_battery():
		laptop = True

	ico = Image.open('pos-terminal.png')
	
	try:
		m = mcp.MCP()
		mcp_t = threading.Thread(target=info_screen)
		mcp_t.start()
		
		tray = pystray.Icon("example", icon=ico,
						menu=pystray.Menu(
							pystray.MenuItem("Info", on_click),
							pystray.MenuItem("Battery", on_click),
							pystray.MenuItem("Exit", on_exit)))

		tray.run()
	except Exception as e:
		print(e)
