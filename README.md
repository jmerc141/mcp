Circuitpython project to display computer info (CPU, RAM, Disk, Network) on MCP OLED

Create exe:

```powershell
pyinstaller --clean -F --add-data font5x8.bin:. --add-data "python -c "import site; print(''.join(site.getsitepackages()[1]))"\*_imports.json:." --add-data res\icon.png:res --icon=res\icon.png --collect-all adafruit_blinka main.py
```
For GPIO:

```python
    mcpa = PyMCP2221A.PyMCP2221A()
    print('PyMCP2221A:', dir(mcpa))

    mcpe = EasyMCP2221.Device()
    print(mcpe)

    print('board:', dir(board))

    led = digitalio.DigitalInOut(board.G0)
    led.direction = digitalio.Direction.OUTPUT
    
    while True:
        led.value = True
        time.sleep(2)
        led.value = False
        time.sleep(2)
```
