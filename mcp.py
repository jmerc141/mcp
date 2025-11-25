"""
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
display.text("Hello World", 0, 0, 1)    # draw some text at x=0, y=0, colour=1
display.scroll(20, 0)                   # scroll 20 pixels to the right
display.circle(60, 10, 10, 1)

display.buffer                          # byte array
display.buf                             # also byte array
dispaly.rotation                        # current rotation (doesnt work)
display.stride                          # width?
display.format                          # fill, fill_rect, get_pixel, set_pixel
display.blit                            # not implemented
"""
import board, busio, adafruit_ssd1306
from PIL import Image

class MCP:

    running = True
    
    # Adjust image_ratio for width of jpg images
    image_ratio = 60

    def __init__(self):
        
        i2c = busio.I2C(board.SCL, board.SDA)
        
        self.w = 128
        self.h = 64

        self.display = adafruit_ssd1306.SSD1306_I2C(self.w, self.h, i2c)

        self.display.fill(0)

        self.display.show()
        

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

        #final_image.close()
        #im.close()

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

    """
    
    """
    batline = 54
    def battery(self, info):
        self.display.fill(0)
        bar = int(self.h - (info['percent'] / 100) * self.h)
        self.display.text(f"{info['percent']}%", 5, 0, 1)
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

        self.display.show()


    dsk_offset = 62
    
    def disk(self, info: list):
        self.display.text(f"Disk0 MB/s", self.dsk_offset, 0, 1)
        self.display.text(f"Read: {info[0]:05.1f}", self.dsk_offset, 10, 1)
        self.display.text(f"Writ: {info[1]:05.1f}", self.dsk_offset, 18, 1)


    def net(self, info: list):
        self.display.text(f"NetIO Mb/s", self.dsk_offset, 34, 1)
        self.display.text(f"Recv: {info[0]:05.1f}", self.dsk_offset, 44, 1)
        self.display.text(f"Send: {info[1]:05.1f}", self.dsk_offset, 52, 1)


    def clear(self):
        self.display.fill(0)
        self.display.show()
    
    
