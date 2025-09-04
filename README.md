pip install hidapi, adafruit-blinka, adafruit-circuitpython-ssd1306

set BLINKA_MCP2221=1

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
