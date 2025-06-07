'''
pip install hidapi, adafruit-blinka, adafruit-circuitpython-ssd1306
set BLINKA_MCP2221=1
'''

#import EasyMCP2221, board, os, digitalio, busio, time, adafruit_ssd1306
import board, busio, adafruit_ssd1306
#from PyMCP2221A import PyMCP2221A



def bar():
    x = 0

    while True:
        for col in range(0, x):
            for row in range(0, 10):
                display.pixel(col, row, 1)
        time.sleep(1)
        print('up')
        x += 1
        

        display.show()


if __name__ == '__main__':

    '''
    print(os.environ['BLINKA_MCP2221'])

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
    '''

    '''
        display.poweroff()     # power off the display, pixels persist in memory
        display.poweron()      # power on the display, pixels redrawn
        display.contrast(0)    # dim
        display.contrast(255)  # bright
        display.invert(1)      # display inverted
        display.invert(0)      # display normal
        display.rotate(True)   # rotate 180 degrees
        display.rotate(False)  # rotate 0 degrees
        display.show()         # write the contents of the FrameBuffer to display memory

        display.fill(0)                         # fill entire screen with colour=0
        display.pixel(0, 10)                    # get pixel at x=0, y=10
        display.pixel(0, 10, 1)                 # set pixel at x=0, y=10 to colour=1
        display.hline(0, 8, 4, 1)               # draw horizontal line x=0, y=8, width=4, colour=1
        display.vline(0, 8, 4, 1)               # draw vertical line x=0, y=8, height=4, colour=1
        display.line(0, 0, 127, 63, 1)          # draw a line from 0,0 to 127,63
        display.rect(10, 10, 107, 43, 1)        # draw a rectangle outline 10,10 to 117,53, colour=1
        display.fill_rect(10, 10, 107, 43, 1)   # draw a solid rectangle 10,10 to 117,53, colour=1
        display.text('Hello World', 0, 0, 1)    # draw some text at x=0, y=0, colour=1
        display.scroll(20, 0)                   # scroll 20 pixels to the right
        display.circle(60, 10, 10, 1)
    '''

    # Init MCP board
    i2c = busio.I2C(board.SCL, board.SDA)
    # Init
    w = 128
    h = 32
    display = adafruit_ssd1306.SSD1306_I2C(w, h, i2c)

    display.fill(0)

    display.show()

    from PIL import Image
    im = Image.open('C:\\Users\\james\\Pictures\\xbox.jpg')
    
    im_ratio = im.width / im.height
    target_w, target_h = (w, h)
    target_ratio = target_w / target_h

    print(im_ratio, target_ratio)

    if im_ratio > target_ratio:
        # Image is wider
        new_width = target_w
        new_height = int(target_w / im_ratio)
    else:
        # Image is taller
        new_height = target_h
        new_width = int(target_h * im_ratio) + 10
    
    resized = im.resize((new_width, new_height), Image.LANCZOS)
    print(im.size, 'resized to', resized.size)
    # Create a new black background image
    new_image = Image.new('RGB', (128,32), (0, 0, 0))
    paste_position = (
        (target_w - new_width) // 2,
        (target_h - new_height) // 2
    )
    
    print(resized.size)
    new_image.paste(resized, paste_position)
    
    display.image(new_image.convert('1'))
    resized.save('im.png')
    new_image.save('pic.png')
    
    display.show()

    new_image.close()
    im.close()

    '''
    'blit', 'buf', 'circle', 'fill', 'fill_rect', 'format', 'hline', 
    'image', 'line', 'pixel', 'rect', 'rotation', 'scroll', 'stride', 'text', 'vline', 
    '''

    
    
    