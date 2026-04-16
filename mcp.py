"""
display.poweroff()	 # power off the display, pixels persist in memory
display.poweron()	  # power on the display, pixels redrawn
display.contrast(0)	# dim
display.contrast(255)  # bright
TODO: top 5 processes?
"""
import s_probe, board, busio, adafruit_ssd1306, time, psutil, \
	subprocess, math, threading
from PIL import Image
from collections import defaultdict

class MCP:
	mcp_running = True
	# Disk number
	n=0
	# Adjust image_ratio for width of jpg images, higher = wider
	image_ratio = 72
	disk_idle = 0
	

	def __init__(self):
		i2c = busio.I2C(board.SCL, board.SDA)
		self.w = 128
		self.h = 64
		self.hhalf = self.h//2
		self.whalf = self.w//2
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
		Start typeperf thread to get disk active time %
	'''
	def start_disk_time(self):
		self.disk_thread = threading.Thread(target=self.popen)
		self.disk_thread.start()


	'''
		For pyinstaller to not make a console window.
		Gets disk active time from typeperf
	'''
	def popen(self):
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		self.process = subprocess.Popen(['typeperf', f'\\PhysicalDisk(_Total)\\% Idle Time'],
			startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
		for l in self.process.stdout:
			res_string = l.decode().split(',')[-1].replace('"', '').strip()
		
			try:
				self.disk_idle = abs(100.0 - float(res_string))
			except ValueError as ve:
				self.disk_idle = 0
		
		time.sleep(1)


	'''
		Stop disk typeperf process and thread
	'''
	def stop_disk_time(self):
		self.process.kill()
		self.disk_thread.join()


	'''
		Gets disk read / write bytes
		Blocks execution for 1s to get accurate reading
	'''
	def diskio(self, prev):
		disks = psutil.disk_io_counters(perdisk=True)

		#rb = disks[f'PhysicalDrive{self.n}'].read_bytes
		#wb = disks[f'PhysicalDrive{self.n}'].write_bytes
		#rt = disks[f'PhysicalDrive{n}'].read_time
		#wt = disks[f'PhysicalDrive{n}'].write_time

		#time.sleep(1)
		rb = prev[f'PhysicalDrive{self.n}'].read_bytes
		wb = prev[f'PhysicalDrive{self.n}'].write_bytes

		read = round((disks[f'PhysicalDrive{self.n}'].read_bytes - rb) / 1000000, 2)
		writ = round((disks[f'PhysicalDrive{self.n}'].write_bytes - wb) / 1000000, 2)
		#rt = disks[f'PhysicalDrive{n}'].read_time - rt
		#wt = disks[f'PhysicalDrive{n}'].write_time - wt

		return [read, writ]#, rt, wt]


	'''
		TODO: Currently using the first network interface in the index [0]
		Takes previous net reading as argument
		Returns float as Mb/s
		This funtion must be called every 1 second for accuracy
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
			new_width = int(im_ratio * self.image_ratio)
		
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
	
	
	'''
		Displays CPU, RAM, disk and net info on oled
		CPU, Net and Disk info must run every 1 second.
		CPU info is collected about every 1.2s, net and disk info are collected every 1s
	'''
	def info_screen(self):
		vline = 58
		cpu_offset = 0
		cpu_width = 26
		ram_offset = 28
		ram_width = 26
		dsk_offset = 62
		net_info = [0,0]
		disk_info = [0,0]
		while self.mcp_running:
			st = time.perf_counter()
			self.display.fill(0)
			
			netb = psutil.net_io_counters(pernic=True)[self.net_interfaces[0]]
			diskb = psutil.disk_io_counters(perdisk=True)
			
			cpu = psutil.cpu_percent(interval=0)
			ram = psutil.virtual_memory().percent

			cpu_i = int(self.h - (cpu / 100) * self.h + 5)
			self.display.text(f"{cpu:.0f}%", cpu_offset+4, 0, 1)
			self.display.text(f"CPU", cpu_offset+4, 10, 1)
			# Outer rect
			self.display.rect(cpu_offset, 8, cpu_width, self.h, 1)
			# Inner rect
			self.display.fill_rect(cpu_offset+2, cpu_i, cpu_width-4, self.h-cpu-2, 1)
			
			self.display.text(f"{ram:.0f}%", ram_offset+4, 0, 1)
			self.display.text(f"RAM", ram_offset+4, 10, 1)
			ram_i = int(self.h - (ram / 100) * self.h)
			self.display.rect(ram_offset, 8, ram_width, self.h, 1)
			self.display.fill_rect(ram_offset+2, ram_i+2, ram_width-4, self.h-ram_i-4, 1)

			self.display.vline(vline, 0, self.h, 1)

			self.display.text(f"Disk0 MB/s", dsk_offset, 0, 1)
			self.display.text(f"Read: {disk_info[0]:05.1f}", dsk_offset, 10, 1)
			self.display.text(f"Writ: {disk_info[1]:05.1f}", dsk_offset, 18, 1)

			self.display.hline(vline, self.hhalf, self.w, 1)
			
			self.display.text(f"NetIO Mb/s", dsk_offset, 34, 1)
			self.display.text(f"Recv: {net_info[0]:05.1f}", dsk_offset, 44, 1)
			self.display.text(f"Send: {net_info[1]:05.1f}", dsk_offset, 52, 1)
			
			# 0.2s
			self.update()

			# Ensure info collection time is 1s for accurate readings
			elap = time.perf_counter() - st
			if elap < 1:
				time.sleep(1-elap)
			net_info = self.netio(netb)
			disk_info = self.diskio(diskb)


	'''
		Function that draws rectangles of hardware readings in corresponding box
	'''
	def fill_graph(self, start_pos, lst):
		for l in lst:
			y_and_height = int(self.h - (l/100) * self.h + 8)
			self.display.fill_rect(start_pos, y_and_height, 1, self.h, 1)
			start_pos -= 1
		lst.pop(-1)


	'''
		Function specific to the bottom half of Net graph
	'''
	def fill_half_graph(self, start_pos, div, lst):
		for l in lst:
							 # StartY - Percent *  Max height
			x_and_height = int(self.h - (l/div) * (self.h/2.5))
			#print('bottom', l, l/div, x_and_height)
			self.display.fill_rect(start_pos, x_and_height, 1, x_and_height, 1)
			start_pos -= 1
		lst.pop(-1)


	'''
		Fills the upper part of net graph for uploads
	'''
	def fill_up_graph(self, start_pos, div, lst):
		for l in lst:
					# StartY   - Percent *  Max height
			h = int(self.hhalf - (l/div) * (self.h/2.5))
			# +4 for offset
			self.display.fill_rect(start_pos, h+4, 1, self.hhalf-h, 1)
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
		net = [0,0]
		# Start disk typeperf thread
		self.start_disk_time()
		while self.mcp_running:
			st = time.perf_counter()
			cpu_graph_start_pos = 29
			ram_graph_start_pos = cpu_graph_start_pos + 32
			dsk_graph_start_pos = ram_graph_start_pos + 32
			net_graph_start_pos = dsk_graph_start_pos + 33
			
			self.display.fill(0)

			# elap must be 1 second for accurate CPU and net measurments, netio() must be run after 1s
			# disk is handled in seperate thread and ram is not time dependent
			
			netb = psutil.net_io_counters(pernic=True)[self.net_interfaces[0]]
			cpu = psutil.cpu_percent(interval=0)
			ram = psutil.virtual_memory().percent
			
			cpu_hist.insert(0, cpu)
			ram_hist.insert(0, ram)
			dsk_hist.insert(0, self.disk_idle)
			down_hist.insert(0, net[0])
			up_hist.insert(0, net[1])

			self.display.text(f"{cpu:>3.0f}%", 3, 0, 1)
			self.display.text(f"CPU", 6, 10, 1)

			self.display.text(f"{ram:>3.0f}%", 34, 0, 1)
			self.display.text(f"RAM", 38, 10, 1)

			self.display.text(f"{self.disk_idle:>3.0f}%", 65, 0, 1)
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
			self.fill_up_graph(net_graph_start_pos, self.net_up_speed, up_hist)
			
			self.update()

			elap = time.perf_counter() - st
			if elap < 1:
				time.sleep(1-elap)

			net = self.netio(netb)
			
		self.stop_disk_time()


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


	def digital_clock(self):
		while self.mcp_running:
			self.display.fill(1)
			self.display.fill_rect(10, 5, self.w-20, self.h-10, 0)
			self.display.text(f'{time.strftime('%I:%M\n%S:%p')}', 20, 10, 1, size=3)
			#print(time.strftime('%I:%M:%p'), end='\r')
			self.update()
			time.sleep(1)


	'''
		Display analog / digital clock screen
	'''
	def analog_clock(self):
		clock_center_x = int(self.w/4)-1
		clock_center_y = self.hhalf
		sec_length = clock_center_y - 1
		min_length = clock_center_y - 8
		hr_length  = clock_center_y - 16
		
		while self.mcp_running:
			st = time.perf_counter()

			self.display.fill(0)
			#self.display.fill_rect(10, 5, self.w-20, self.h-10, 0)
			self.display.circle(clock_center_x, clock_center_y, 2, 1)
			# Tick marks
			self.display.line(clock_center_x, clock_center_y-30, clock_center_x,  clock_center_y-24, 1)
			self.display.line(clock_center_x, clock_center_y+24, clock_center_x, clock_center_y+30, 1)
			self.display.line(clock_center_x-30, clock_center_y, clock_center_x-24, clock_center_y, 1)
			self.display.line(clock_center_x+24, clock_center_y, clock_center_x+30, clock_center_y, 1)
			self.display.circle(clock_center_x+12, clock_center_y-24, 2, 1)
			self.display.circle(clock_center_x+22, clock_center_y-14, 2, 1)
			self.display.circle(clock_center_x+22, clock_center_y+14, 2, 1)
			self.display.circle(clock_center_x+12, clock_center_y+24, 2, 1)
			self.display.circle(clock_center_x-12, clock_center_y+24, 2, 1)
			self.display.circle(clock_center_x-22, clock_center_y+14, 2, 1)
			self.display.circle(clock_center_x-22, clock_center_y-14, 2, 1)
			self.display.circle(clock_center_x-12, clock_center_y-24, 2, 1)
			# Main outer circle
			self.display.circle(clock_center_x, clock_center_y, 32, 1)

			self.display.vline(self.whalf+1, 0, self.h, 1)

			# Second hand
			sec = int(time.strftime('%S'))
			angle = (sec / 60) * 2 * math.pi
			endx = int(clock_center_x + math.sin(angle) * sec_length)
			endy = int(clock_center_y - math.cos(angle) * sec_length)
			self.display.line(clock_center_x, clock_center_y, endx, endy, 1)

			# Minute hand TODO: add seconds to minute hand and minutes to hour hand
			m = int(time.strftime('%M')) + sec / 60
			#print(m, sec, sec/60)
			angle = (m / 60) * 2 * math.pi
			endx = int(clock_center_x + math.sin(angle) * min_length)
			endy = int(clock_center_y - math.cos(angle) * min_length)
			self.display.line(clock_center_x, clock_center_y, endx, endy, 1)

			# Hour hand
			h = int(time.strftime('%H')) + m / 60
			angle = (h / 12) * 2 * math.pi
			endx = int(clock_center_x + math.sin(angle) * hr_length)
			endy = int(clock_center_y - math.cos(angle) * hr_length)
			self.display.line(clock_center_x, clock_center_y, endx, endy, 1)

			self.display.text(f'{time.strftime('H:%I')}', self.whalf+12, 0, 1, size=2)
			self.display.text(f'{time.strftime('M:%M')}', self.whalf+12, 20, 1, size=2)
			self.display.text(f'{time.strftime('S:%S')}', self.whalf+12, 40, 1, size=2)
			self.display.text(f'{time.strftime('%p')}', self.whalf+30, 55, 1, size=1)

			self.update()

			elap = time.perf_counter() - st
			if elap < 1:
				time.sleep(1-elap)


	'''
		Show list of top 7 processes
		TODO: psutil.process_iter() is slow when not run as admin, maybe implement in different way
	'''
	def processes(self):
		self.clear()

		while self.mcp_running:
			self.display.fill(0)
			st = time.perf_counter()
			# 1.2s
			procs = []
			for p in psutil.process_iter(['name', 'memory_info']):
				try:
					p.cpu_percent(None)
					procs.append(p)
				except psutil.NoSuchProcess as nsp:
					pass
			
			time.sleep(1)
			
			p_group = defaultdict(lambda: {
				"ram_mb": 0.0,
				"cpu": 0.0,
				"count": 0
			})

			# 1s
			stats = []
			for p in procs:
				try:
					name = p.info['name'] or 'N/A'
					ramMB = p.memory_info().rss / 1024**2
					cpu = p.cpu_percent()

					p_group[name]['ram_mb'] += ramMB
					p_group[name]['cpu'] += cpu // psutil.cpu_count(logical=False)
					p_group[name]['count'] += 1
				except psutil.NoSuchProcess as nsp:
					pass
			

			stats = []
			for name, data in p_group.items():
				if name == 'System Idle Process':
					pass
				else:
					stats.append({
						"name": name.replace('.exe', '').replace('.EXE', ''),
						"ram_mb": data["ram_mb"],
						"cpu": data["cpu"],
						"count": data["count"]
					})
			
			# Sort by ram usage
			#stats.sort(key=lambda x: x['ram_mb'], reverse=True)
			# Sort by cpu usage
			stats.sort(key=lambda x: x['cpu'], reverse=True)
			
			stats = stats[:7]

			#elap = time.perf_counter() - st
			#print(elap)

			self.display.hline(0, 7, self.w, 1)
			self.display.text('Process', 0, 0, 1)
			self.display.vline(self.whalf-14, 0, self.h, 1)
			self.display.text('CPU%', self.whalf-10, 0, 1)
			self.display.vline(self.whalf+18, 0, self.h, 1)
			self.display.text('RAM(MB)', self.whalf+22, 0, 1)

			for i,p in enumerate(stats):
				self.display.text(f'{p['name']:^8.8}', 0, 8+i*8, 1)
				self.display.text(f'{p['cpu']:^3.0f}', self.whalf-6, 8+i*8, 1)
				self.display.text(f'{p['ram_mb']:<6.2f}', self.whalf+22, 8+i*8, 1)
				#print(f'{p['name']}, {p['ram_mb']}MB {p['cpu']}% {p['count']}')
					
			self.update()


	'''
		Safely update the diplay
	'''
	def update(self):
		try:
			self.display.show()
		except OSError as o:
			#print('Unplugged')
			self.on_exit()


	def clear(self):
		self.display.fill(0)
		self.update()

	
	def kill_sprobe(self):
		s_probe.sProbe.on_close()
	
	
