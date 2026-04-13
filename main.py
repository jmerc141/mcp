'''
	Only supporting windows, not sure about MCP linux drivers
'''

'''
	Set enviroment var
'''
import os, sys, subprocess
if 'BLINKA_MCP2221' not in os.environ:
	os.environ['BLINKA_MCP2221'] = '1'

import mcp, frame_extractor, psutil, pystray, threading, pathlib, easygui, \
	shutil
from PIL import Image

laptop = False
frame_folder = ''
menu_labels = ["Graphs", "Detail", "Processes", "Battery", "Clock", "Image", "Video"]
current_state = menu_labels[0]


'''
	Displays on system with no battery
'''
def no_bat():
	m.clear()
	m.display.text('No battery\n  detected', 5, 12, 1, size=2)
	m.display.show()


'''
	Shows a static image file
'''
def display_image():
	m.clear()
	m.display.text('Choose an image file', 10, 12, 1)
	m.display.show()
	m.show_image(easygui.fileopenbox())


'''
	Shows file dialogue, extracts frames, and shows video
'''
def video():
	global frame_folder
	m.clear()
	m.display.text('Choose a video file', 10, 12, 1)
	m.display.show()

	vid_path = easygui.fileopenbox()
	if vid_path == None:
			m.info_screen()
	else:
		frame_folder = pathlib.Path(vid_path).name.split('.')[0]
		try:
			os.makedirs(frame_folder)
		except FileExistsError as fe:
			frame_folder = f'frames{random.randint(0,100)}'
			os.makedirs(frame_folder)
		frame_extractor.exctract_frame_cli(vid_path, m, frame_folder)
		m.vid(frame_folder, pathlib.Path(frame_folder).iterdir())


'''
	Runs on exit, stop threads and removes temp folders
'''
def on_exit(icon):
	global frame_folder
	m.mcp_running = False
	mcp_t.join()
	m.kill_sprobe()
	m.clear()
	try:
		shutil.rmtree(frame_folder)
	except FileNotFoundError as fnf:
		pass
	icon.stop()


'''
	Defines check mark state
'''
def is_selected(value):
	return lambda item: current_state == value


'''
	Runs on tray click, passes text as argument
'''
def on_click(icon, item):
	m.clear()
	global mcp_t, current_state
	m.mcp_running = False
	target = ''
	
	mcp_t.join()
	
	if item.text == 'Detail':
		target = m.info_screen
	elif item.text == 'Graphs':
		target = m.graphs
	elif item.text == 'Battery':
		if laptop:
			target = m.bat_screen
		else:
			target = no_bat
	elif item.text == 'Image':
		target = display_image
	elif item.text == 'Video':
		target = video
	elif item.text == 'Clock':
		target = m.analog_clock
	elif item.text == 'Processes':
		target = m.processes

	current_state = item.text

	mcp_t = threading.Thread(target=target)
	if not mcp_t.is_alive():
		m.mcp_running = True
		mcp_t.start()


if __name__ == '__main__':
	if psutil.sensors_battery():
		laptop = True

	if hasattr(sys, '_MEIPASS'):
		os.chdir(sys._MEIPASS)

	ico = Image.open('res/icon.png')
	
	try:
		m = mcp.MCP()
		mcp_t = threading.Thread(target=m.graphs)
		mcp_t.start()
		
		# Create tray menu items
		mis = []
		for i in menu_labels:
			mis.append(pystray.MenuItem(i, on_click, checked=is_selected(i), radio=True))
		mis.append(pystray.MenuItem("Exit", on_exit))
		
		tray = pystray.Icon("MCP", icon=ico, menu=pystray.Menu(*mis))

		tray.run()
	except Exception as e:
		#print(e)
		pass
