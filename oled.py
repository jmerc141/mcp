psutil.cpu_percent(percpu=True), psutil.virtual_memory(),
psutil.cpu_freq(), 

len(psutil.disk_io_counters(perdisk=True))


import psutil, time, pystray
from PIL import Image, ImageDraw


n=0

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

	print(f'\33[2K\r{read}MB {writ}MB {rt}ms {wt}ms', end='')


def netio():
	netb = psutil.net_io_counters(pernic=True)['Ethernet']

	time.sleep(1)

	net = psutil.net_io_counters(pernic=True)['Ethernet']

	# / 125000 for Mb, / 1_000_000
	nettx = round(((net.bytes_sent - netb.bytes_sent) / 125_000), 3)
	netrx = round(((net.bytes_recv - netb.bytes_recv) / 125_000), 3)
	if (net.bytes_sent - netb.bytes_sent) * 8 > 1_000_000:
		print(f'\r{netrx}Mb/s Down {nettx}Mb/s Up', end='')
	else:
		print(f'\r{netrx}Kb/s Down {nettx}Kb/s Up', end='')	


def bat():
	if psutil.sensors_battery():
		print(psutil.sensors_battery())


def on_exit(icon):
      icon.stop()


def on_click():
	print("Hello World")
	time.sleep(2)


if __name__ == '__main__':
	ico = Image.open('pos-terminal.png')

	tray = pystray.Icon("example", icon=ico,
					menu=pystray.Menu(
						pystray.MenuItem("Say Hello", on_click),
						pystray.MenuItem("Exit", on_exit)))
	print(dir(tray))
	tray.run()
	
