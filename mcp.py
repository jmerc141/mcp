"""
display.poweroff()	 # power off the display, pixels persist in memory
display.poweron()	  # power on the display, pixels redrawn
display.contrast(0)	# dim
display.contrast(255)  # bright
display.invert(1)	  # display inverted
display.invert(0)	  # display normal
display.rotate(True)   # rotate 180 degrees
display.rotate(False)  # rotate 0 degrees
display.show()		 # write the contents of the FrameBuffer to display memory

display.fill(0)						 # fill entire screen with colour=0
display.pixel(0, 10)					# get pixel at x=0, y=10
display.pixel(0, 10, 1)				 # set pixel at x=0, y=10 to colour=1
display.hline(0, 8, 4, 1)			   # draw horizontal line x=0, y=8, width=4, colour=1
display.vline(0, 8, 4, 1)			   # draw vertical line x=0, y=8, height=4, colour=1
display.line(0, 0, 127, 63, 1)		  # draw a line from 0,0 to 127,63
display.rect(10, 10, 107, 43, 1)		# draw a rectangle outline 10,10 to 117,53, colour=1
display.fill_rect(10, 10, 107, 43, 1)   # draw a solid rectangle 10,10 to 117,53, colour=1
display.text("Hello World", 0, 0, 1)	# draw some text at x=0, y=0, colour=1
display.scroll(20, 0)				   # scroll 20 pixels to the right
display.circle(60, 10, 10, 1)

display.buffer						  # byte array
display.buf							 # also byte array
dispaly.rotation						# current rotation (doesnt work)
display.stride						  # width?
display.format						  # fill, fill_rect, get_pixel, set_pixel
display.blit							# not implemented
"""
import board, busio, adafruit_ssd1306, time, psutil, subprocess, \
	s_probe
from PIL import Image


class MCP:
	mcp_running = True
	# Disk number
	n=0
	# Adjust image_ratio for width of jpg images
	image_ratio = 60

	
	def __init__(self):
		i2c = busio.I2C(board.SCL, board.SDA)
		self.w = 128
		self.h = 64
		self.display = adafruit_ssd1306.SSD1306_I2C(self.w, self.h, i2c)
		self.display.fill(0)
		self.display.show()

		self.net_interfaces = []
		for interface in psutil.net_io_counters(pernic=True):
			self.net_interfaces.append(interface)

		# Mb/s
		self.net_up_speed = 150
		self.net_down_speed = 150

		# TODO: add abaility to switch disk being monitored
		res = subprocess.run(['typeperf', f'\\PhysicalDisk(*)\\*', '-sc', '1'],
		capture_output=True, text=True)
		self.phys_disks = set()
		for d in res.stdout.split('\n')[1].split('\\'):
			if 'PhysicalDisk' in d:
				self.phys_disks.add(d)
		

	'''
		Gets disk read / write bytes
		Blocks execution for 1s to get accurate reading
	'''
	def diskio(self):
		disks = psutil.disk_io_counters(perdisk=True)

		rb = disks[f'PhysicalDrive{self.n}'].read_bytes
		wb = disks[f'PhysicalDrive{self.n}'].write_bytes
		#rt = disks[f'PhysicalDrive{n}'].read_time
		#wt = disks[f'PhysicalDrive{n}'].write_time

		time.sleep(1)

		disks = psutil.disk_io_counters(perdisk=True)

		read = round((disks[f'PhysicalDrive{self.n}'].read_bytes - rb) / 1000000, 2)
		writ = round((disks[f'PhysicalDrive{self.n}'].write_bytes - wb) / 1000000, 2)
		#rt = disks[f'PhysicalDrive{n}'].read_time - rt
		#wt = disks[f'PhysicalDrive{n}'].write_time - wt

		return [read, writ]#, rt, wt]


	'''
		Gets disk active time
		Blocks execution for 1s to get accurate reading
		Currently gets all disks on system (Total)
		TODO takes 1.3 seconds
	'''
	def disk_time(self):
		try:
			res = subprocess.run(['typeperf', f'\\PhysicalDisk(_Total)\\% Idle Time', '-sc', '1'],
				capture_output=True, text=True)
			res_string = res.stdout.split('\n')[2].split(',')[1].strip('"')
		except IndexError as ie:
			print(ie)
			return 0
		
		return abs(100.0 - float(res_string))


	'''
		TODO: Currently using the first network interface in the index [0]
		Returns float as Mb/s
	'''
	def netio(self, prev):
		#global netb
		#netb = psutil.net_io_counters(pernic=True)['Ethernet']
		#time.sleep(1)
		net = psutil.net_io_counters(pernic=True)[self.net_interfaces[0]]

		# / 125000 for Mb, / 1_000_000
		nettx = round(((net.bytes_sent - prev.bytes_sent) / 125_000), 3)
		netrx = round(((net.bytes_recv - prev.bytes_recv) / 125_000), 3)

		return [netrx, nettx]

		#if (net.bytes_sent - prev.bytes_sent) * 8 > 1_000_000:
		#	print(f'\r{netrx}Mb/s Down {nettx}Mb/s Up', end='')
		#else:
		#print(f'\r{netrx}Kb/s Down {nettx}Kb/s Up', end='')	

	"""
		Display an image
	"""
	def show_image(self, im_path):
		im = Image.open(im_path)
		
		im_ratio = im.width / im.height
		target_w, target_h = (self.w, self.h)
		target_ratio = target_w / target_h

		if im_ratio > target_ratio:
			# Image is wider (this is uncommon)
			new_width = target_w
			new_height = int(target_w / im_ratio)
		else:
			# Image is taller
			new_height = target_h
			new_width = int(im_ratio * 60)
		
		resized = im.resize((new_width, new_height), Image.LANCZOS)
		#print(im.size, "resized to", resized.size)

		# Create a new black background image
		final_image = Image.new("RGB", (self.w, self.h), (0, 0, 0))
		
		paste_position = (
			(target_w - new_width) // 2,
			(target_h - new_height) // 2
		)
		
		final_image.paste(resized, paste_position)
		self.display.image(final_image.convert("1"))
		
		#resized.save("im.png")
		#new_image.save("pic.png")
		
		self.display.show()

		final_image.close()
		im.close()


	'''
		Loop through frames to show video
	'''
	def vid(self, frame_folder, iter):
		for f in iter:
			if self.mcp_running:
				self.show_image(f'{f}')
	

	'''
		Displays a progress bar screen for extracting video frames
	'''
	def progress_bar(self, percent: float):
		#print(percent, end='\r')
		self.display.fill(0)
		self.display.text('Extracting frames...', 5, 10, 1)
		self.display.rect(5, 40, self.w-5, 20, 1)
		self.display.text(f"{percent*100:.0f}%", 48, 26, 1)
		self.display.fill_rect(8, 42, int(percent * self.w)-8, 16, 1)
		self.display.show()


	"""

	"""
	cpu_offset = 0
	cpu_width = 26
	def cpu_bar(self, percent: float):
		tmp = int(self.h - (percent / 100) * self.h + 5)
		# Text shows cpu percent
		self.display.text(f"{percent:.0f}%", self.cpu_offset+4, 0, 1)
		self.display.text(f"CPU", self.cpu_offset+4, 10, 1)
		# Outer rect (x, y, width, length, color)
		self.display.rect(self.cpu_offset, 8, self.cpu_width, self.h, 1)
		# Inner rect
		self.display.fill_rect(self.cpu_offset+2, tmp, self.cpu_width-4, self.h-tmp-2, 1)

	"""
	
	"""
	ram_offset = 28
	ram_width = 26
	def ram(self, percent: float):
		self.display.text(f"{percent:.0f}%", self.ram_offset+4, 0, 1)
		self.display.text(f"RAM", self.ram_offset+4, 10, 1)
		tmp = int(self.h - (percent / 100) * self.h)
		# Outer rect (x, y, width, length, color)
		self.display.rect(self.ram_offset, 8, self.ram_width, self.h, 1)
		# Inner rect
		self.display.fill_rect(self.ram_offset+2, tmp+2, self.ram_width-4, self.h-tmp-4, 1)



	dsk_offset = 62
	
	def disk(self, info: list):
		self.display.text(f"Disk0 MB/s", self.dsk_offset, 0, 1)
		self.display.text(f"Read: {info[0]:05.1f}", self.dsk_offset, 10, 1)
		self.display.text(f"Writ: {info[1]:05.1f}", self.dsk_offset, 18, 1)


	def net(self, info: list):
		self.display.text(f"NetIO Mb/s", self.dsk_offset, 34, 1)
		self.display.text(f"Recv: {info[0]:05.1f}", self.dsk_offset, 44, 1)
		self.display.text(f"Send: {info[1]:05.1f}", self.dsk_offset, 52, 1)

	
	'''
		Displays CPU, RAM, disk and net info on oled
		Does not need time.sleep, collecting info takes about 1s
	'''
	def info_screen(self):
		vline = 58
		while self.mcp_running:
			st = time.perf_counter()
			netb = psutil.net_io_counters(pernic=True)[self.net_interfaces[0]]
			self.display.fill(0)

			self.cpu_bar(psutil.cpu_percent(interval=0))

			self.ram(psutil.virtual_memory().percent)

			self.display.vline(vline, 0, self.h, 1)

			self.disk(self.diskio())

			self.display.hline(vline, self.h//2, self.w, 1)

			self.net(self.netio(netb))

			elap = time.perf_counter() - st
			
			# Ensure info collection time is 1s for accurate readings
			if elap < 1:
				time.sleep(1-elap)
			
			# 0.2s
			self.update()


	'''
		Function that draws rectangles of hardware readings in corresponding box
	'''
	def fill_graph(self, start_pos, lst):
		for l in lst:
			x_and_height = int(self.h - (l/100) * self.h + 5)
			self.display.fill_rect(start_pos, x_and_height, 1, x_and_height, 1)
			start_pos -= 1
		lst.pop(-1)


	'''
		Function specific to the bottom hlaf of Net graph
	'''
	def fill_half_graph(self, start_pos, div, lst):
		for l in lst:
			x_and_height = int(self.h - (l/div) * (self.h/2.5))
			self.display.fill_rect(start_pos, x_and_height, 1, x_and_height, 1)
			start_pos -= 1
		lst.pop(-1)


	'''
		Graphs of info
		TODO: make scrolling y-max for disk/network graphs
	'''
	def graphs(self):
		cpu_hist = [0] * 28
		ram_hist = [0] * 28
		dsk_hist = [0] * 28
		down_hist = [0] * 28
		up_hist  = [0] * 28
		hlinex = 96
		hliney = 35
		while self.mcp_running:
			cpu_graph_start_pos = 29
			ram_graph_start_pos = cpu_graph_start_pos + 32
			dsk_graph_start_pos = ram_graph_start_pos + 32
			net_graph_start_pos = dsk_graph_start_pos + 33

			self.display.fill(0)
			#st = time.perf_counter()
			netb = psutil.net_io_counters(pernic=True)[self.net_interfaces[0]]
			cpu = psutil.cpu_percent(interval=0)
			ram = psutil.virtual_memory().percent
			disks = self.disk_time()		# Blocks for 1 seconds
			net = self.netio(netb)

			#elap = time.perf_counter() - st
			
			#print(elap)
			#if elap < 1:
			#	time.sleep(1-elap)
			
			cpu_hist.insert(0, cpu)
			ram_hist.insert(0, ram)
			dsk_hist.insert(0, disks)
			down_hist.insert(0, net[0])
			up_hist.insert(0, net[1])

			self.display.text(f"{cpu:>3.0f}%", 3, 0, 1)
			self.display.text(f"CPU", 6, 10, 1)

			self.display.text(f"{ram:>3.0f}%", 34, 0, 1)
			self.display.text(f"RAM", 38, 10, 1)

			self.display.text(f"{disks:>3.0f}%", 65, 0, 1)
			self.display.text(f"Disk", 68, 10, 1)
			
			self.display.text(f"Net", 102, 0, 1)
			self.display.text(f"Up",  104, 8, 1)
			self.display.text(f"Dwn", 102, 36, 1)
			self.display.hline(hlinex, hliney, 30, 1)
			
			# 4 main boxes
			self.display.rect(0, 8, 31, self.h, 1)
			self.display.rect(32, 8, 31, self.h, 1)
			self.display.rect(64, 8, 31, self.h, 1)
			self.display.rect(96, 8, 32, self.h, 1)

			self.fill_graph(cpu_graph_start_pos, cpu_hist)
			self.fill_graph(ram_graph_start_pos, ram_hist)
			self.fill_graph(dsk_graph_start_pos, dsk_hist)
			self.fill_half_graph(net_graph_start_pos, self.net_down_speed, down_hist)
			self.fill_half_graph(net_graph_start_pos, self.net_up_speed, up_hist)
			
			self.update()


	'''
		Displays battery info
	'''
	def bat_screen(self):
		s_probe.sProbe.activate()
		s_probe.sProbe.th.start()
		while self.mcp_running:
			info = {'percent': s_probe.sProbe.chargeRemaining, 'volts': s_probe.sProbe.voltage,
			'amps': s_probe.sProbe.amps, 'watts': s_probe.sProbe.watts,
			'cap': s_probe.sProbe.fullChargeCap, 'health': s_probe.sProbe.health}
			self.battery(info)
			self.update()
			time.sleep(1)


	"""
		Helper function, displays the main battery info
	"""
	batline = 54
	def battery(self, info):
		self.display.fill(0)
		bar = int(self.h - (info['percent'] / 100) * self.h)
		self.display.text(f"{info['percent']}%", 8, 0, 1)
		# Large battery rectangle
		self.display.rect(0, 15, 30, self.h, 1)
		# Small top rectangle
		self.display.rect(10, 10, 10, 6, 1)
		self.display.fill_rect(2, bar+17, 26, self.h-bar-19, 1)
		self.display.vline(self.batline-4, 0, self.h, 1)
		self.display.text(f"Volt: {round(info['volts'], 1)}",self.batline, 0, 1)
		self.display.text(f"Amps: {info['amps']}", self.batline, 10, 1)
		self.display.text(f"Watt: {info['watts']}", self.batline, 20, 1)
		self.display.text(f"Wh  : {info['cap']}", self.batline, 30, 1)
		self.display.text(f"Hlth: {info['health']:.2f}%", self.batline, 40, 1)


	'''
		Safely update the diplay
	'''
	def update(self):
		try:
			self.display.show()
		except OSError as o:
			print('Unplugged')
			self.on_exit()


	def clear(self):
		self.display.fill(0)
		self.display.show()

	
	def kill_sprobe(self):
		s_probe.sProbe.on_close()
	
	
