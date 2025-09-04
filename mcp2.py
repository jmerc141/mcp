import adafruit_displayio_ssd1306, i2cdisplaybus, terminalio, displayio, board, busio, \
time
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font


def run(info):
    while True:
        time.sleep(1)
        print(info)
        text_area.text = f'{info}'


def oled_print(txt):
    _, height, _, dy = font.get_bounding_box()
    for y in range(height):
        pixels = []
        for c in txt:
            glyph = font.get_glyph(ord(c))
            if not glyph:
                continue
            glyph_y = y + (glyph.height - (height + dy)) + glyph.dy

            if 0 <= glyph_y < glyph.height:
                for i in range(glyph.width):
                    value = glyph.bitmap[i, glyph_y]
                    pixel = 0
                    if value > 0:
                        pixel = 1
                    pixels.append(pixel)
            else:
                # empty section for this glyph
                for i in range(glyph.width):
                    pixels.append(0)

            # one space between glyph
            pixels.append(0)
        if pixels:
            for x, pixel in enumerate(pixels):
                bitmap[x, y] = pixel


displayio.release_displays()

w = 128
h = 64

i2c = busio.I2C(board.SCL, board.SDA)
#i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=w, height=h)

# Make the display context
splash = displayio.Group()
display.root_group = splash

color_bitmap = displayio.Bitmap(w, h, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)


# Draw a smaller inner rectangle
# 1-8, 33-56, 
inner_bitmap = displayio.Bitmap(118, 57, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=5, y=4)
splash.append(inner_sprite)

# Display using custom function
bitmap = displayio.Bitmap(40, 20, 2)
font = bitmap_font.load_font('fonts/custom_fonts/Roboto-Medium-8pt.bdf', displayio.Bitmap)
palette = displayio.Palette(2)
palette[0] = 0x000000
palette[1] = 0xFFFFFF
oled_print("Testing!")
tg = displayio.TileGrid(bitmap, pixel_shader=palette, x=20, y=17)
splash.append(tg)



full = 'abcdefghijklmnopqrstuvwxyz'
good_chars = 'ABC!DEFGHJKLMNOPQRSUVWXZ'
bad_chars = 'bde'

# Display using a Label (doesnt work well)
text = 'Hello'
text_area = label.Label(font, text=text, color=0xFFFFFF, x=7, y=10)
#splash.append(text_area)

print('done')

#for c in full:
#    time.sleep(1)
#    text_area.text = f'{c}'
#    print(c, text_area.text, end='\r')

while True:
    time.sleep(1)
    
    