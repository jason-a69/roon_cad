#!/usr/bin/env python3
"""XYTFT-2.0"-SLCM ST7789V2 driver for Raspberry Pi 4.

Item link (2" display)
https://item.taobao.com/item.htm?id=583173435654

Known-good wiring: CS GPIO8, MOSI GPIO10, SCLK GPIO11,
DC GPIO25, RESET GPIO27. Verified landscape is 320x240 at 32 MHz.
Requires: python3-spidev, python3-lgpio, python3-pil.

You user needs to belong to gpio,spi groups
(i.e. sudo usermod -aG gpio,spi $USER)

This driver was written by chatgpt using c++ code it analysed from the Taobao seller.
Be careful with your wiring, it is very sensitive

LCD pin	Wire colour	Raspberry Pi 4 connection (should work for all PIs)
VCC	            🔴 Red	     Physical pin 1 — 3.3V
GND	            ⚫ Black	    Physical pin 6 — GND
SDA / MOSI	    🟡 Yellow	 Physical pin 19 — GPIO10
SCL / SCLK	    🟠 Orange	 Physical pin 23 — GPIO11
CS	            🟢 Green	 Physical pin 24 — GPIO8 / CE0
DC	            🔵 Blue	     Physical pin 22 — GPIO25
RST / RESET	    🟣 Purple	 Physical pin 13 — GPIO27
BL / Backlight	⚪ White	    Physical pin 17 — 3.3V


"""

import time
import spidev
import lgpio
from PIL import Image, ImageChops, ImageDraw, ImageFont


class Display:
    DC = 25
    RST = 27
    SPI_BUS = 0
    SPI_DEVICE = 0
    SPI_SPEED_HZ = 32_000_000

    # degrees: (MADCTL, width, height); 0 is the verified landscape setting.
    _ROTATIONS = {
        0: (0x60, 320, 240),
        90: (0x00, 240, 320),
        180: (0xA0, 320, 240),
        270: (0xC0, 240, 320),
    }

    def __init__(self, spi_speed_hz=SPI_SPEED_HZ):
        self.width, self.height = 320, 240
        self.rotation = 0
        self._closed = False
        self._last_frame = None  # Last frame successfully sent to the display
        self.gpio = lgpio.gpiochip_open(0)
        try:
            lgpio.gpio_claim_output(self.gpio, self.DC, 1)
            lgpio.gpio_claim_output(self.gpio, self.RST, 1)

            self.spi = spidev.SpiDev()
            self.spi.open(self.SPI_BUS, self.SPI_DEVICE)
            self.spi.mode = 0
            self.spi.max_speed_hz = int(spi_speed_hz)
            self.spi.bits_per_word = 8

            self._initialize()
            self.clear("black")
        except Exception:
            if hasattr(self, "spi"):
                self.spi.close()
            lgpio.gpiochip_close(self.gpio)
            raise

    def _command(self, value):
        lgpio.gpio_write(self.gpio, self.DC, 0)
        self.spi.writebytes([value & 0xFF])

    def _data(self, values):
        lgpio.gpio_write(self.gpio, self.DC, 1)
        self.spi.writebytes(list(values))

    def _reset(self):
        lgpio.gpio_write(self.gpio, self.RST, 0)
        time.sleep(0.10)
        lgpio.gpio_write(self.gpio, self.RST, 1)
        time.sleep(0.12)

    def _initialize(self):
        self._reset()
        self._command(0x11)  # Sleep out
        time.sleep(0.12)

        self._command(0x2A)
        self._data([0x00, 0x00, 0x00, 0xEF])
        self._command(0x2B)
        self._data([0x00, 0x28, 0x01, 0x17])

        self._command(0xB2)
        self._data([0x0C, 0x0C, 0x00, 0x33, 0x33])
        self._command(0x20)
        self._command(0xB7)
        self._data([0x56])
        self._command(0xBB)
        self._data([0x18])
        self._command(0xC0)
        self._data([0x2C])
        self._command(0xC2)
        self._data([0x01])
        self._command(0xC3)
        self._data([0x1F])
        self._command(0xC4)
        self._data([0x20])
        self._command(0xC6)
        self._data([0x0F])
        self._command(0xD0)
        self._data([0xA6, 0xA1])

        gamma = [
            0xD0, 0x0D, 0x14, 0x0B, 0x0B, 0x07, 0x3A,
            0x44, 0x50, 0x08, 0x13, 0x13, 0x2D, 0x32
        ]
        self._command(0xE0)
        self._data(gamma)
        self._command(0xE1)
        self._data(gamma)

        self._command(0x36)
        self._data([0x60])  # Verified landscape orientation
        self._command(0x3A)
        self._data([0x66])  # RGB666, 18-bit
        self._command(0xE7)
        self._data([0x00])  # Vendor-specific setting
        self._command(0x21)  # Inversion on
        self._command(0x29)  # Display on
        time.sleep(0.05)

    def set_rotation(self, degrees):
        if degrees not in self._ROTATIONS:
            raise ValueError("Rotation must be 0, 90, 180 or 270")
        madctl, self.width, self.height = self._ROTATIONS[degrees]
        self.rotation = degrees
        self._command(0x36)
        self._data([madctl])

    def _set_window(self):
        self._command(0x2A)
        self._data([0, 0, (self.width - 1) >> 8, (self.width - 1) & 0xFF])
        self._command(0x2B)
        self._data([0, 0, (self.height - 1) >> 8, (self.height - 1) & 0xFF])

    def show(self, image):
        """Display a PIL image, resizing it to the current screen size."""
        if self._closed:
            raise RuntimeError("Display is closed")
        image = image.convert("RGB")
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)

        # RGB666: keep the upper six bits of each 8-bit channel.
        pixels = bytearray(image.tobytes())
        for i in range(len(pixels)):
            pixels[i] &= 0xFC

        self._set_window()
        self._command(0x2C)
        lgpio.gpio_write(self.gpio, self.DC, 1)

        # 3072 bytes per transfer, below the typical spidev buffer limit.
        chunk_bytes = 3072
        for offset in range(0, len(pixels), chunk_bytes):
            self.spi.writebytes2(pixels[offset:offset + chunk_bytes])

        self._last_frame = image.copy()

    def show_region(self, x, y, image):
        """Update only the rectangle occupied by image, at screen position (x, y).

        Pixels outside the display are clipped. The image is sent at its
        native size; it is not resized.
        """
        if self._closed:
            raise RuntimeError("Display is closed")

        image = image.convert("RGB")
        x, y = int(x), int(y)
        left = max(0, x)
        top = max(0, y)
        right = min(self.width, x + image.width)
        bottom = min(self.height, y + image.height)

        if left >= right or top >= bottom:
            return

        # Crop source image to the portion visible on the display.
        crop = image.crop((
            left - x,
            top - y,
            right - x,
            bottom - y,
        ))

        pixels = bytearray(crop.tobytes())
        for i in range(len(pixels)):
            pixels[i] &= 0xFC

        region_width = right - left
        region_height = bottom - top

        self._command(0x2A)
        self._data([left >> 8, left & 0xFF,
                    (right - 1) >> 8, (right - 1) & 0xFF])
        self._command(0x2B)
        self._data([top >> 8, top & 0xFF,
                    (bottom - 1) >> 8, (bottom - 1) & 0xFF])
        self._command(0x2C)
        lgpio.gpio_write(self.gpio, self.DC, 1)

        chunk_bytes = 3072
        for offset in range(0, len(pixels), chunk_bytes):
            self.spi.writebytes2(pixels[offset:offset + chunk_bytes])

        # Keep the cached frame in sync when one is available.
        if self._last_frame is not None:
            self._last_frame.paste(crop, (left, top))

    def show_changed(self, image, tile_size=16):
        """Update multiple changed regions instead of one large bounding box.

        The frame is divided into tiles. Only tiles containing changed pixels
        are sent. Adjacent changed tiles are merged into larger rectangles.
        The first call sends a full frame. Returns the number of rectangles
        transmitted (0 means the image was unchanged).
        """
        if self._closed:
            raise RuntimeError("Display is closed")
        if int(tile_size) < 1:
            raise ValueError("tile_size must be at least 1")
        tile_size = int(tile_size)

        image = image.convert("RGB")
        if image.size != (self.width, self.height):
            image = image.resize(
                (self.width, self.height), Image.Resampling.LANCZOS
            )

        if self._last_frame is None:
            self.show(image)
            return 1

        difference = ImageChops.difference(image, self._last_frame)

        # Find horizontal runs of changed tiles on each tile row.
        row_runs = []
        for top in range(0, self.height, tile_size):
            bottom = min(top + tile_size, self.height)
            runs = []
            run_start = None
            for left in range(0, self.width, tile_size):
                right = min(left + tile_size, self.width)
                changed = difference.crop((left, top, right, bottom)).getbbox()
                if changed and run_start is None:
                    run_start = left
                elif not changed and run_start is not None:
                    runs.append((run_start, top, left, bottom))
                    run_start = None
            if run_start is not None:
                runs.append((run_start, top, self.width, bottom))
            row_runs.append(runs)

        # Merge vertically adjacent runs with identical horizontal bounds.
        rectangles = []
        active = {}
        for runs in row_runs:
            current = {}
            for left, top, right, bottom in runs:
                key = (left, right)
                if key in active:
                    old_top, old_bottom = active[key]
                    current[key] = (old_top, bottom)
                else:
                    current[key] = (top, bottom)

            for key, (old_top, old_bottom) in active.items():
                if key not in current:
                    rectangles.append((key[0], old_top, key[1], old_bottom))
            active = current

        for key, (top, bottom) in active.items():
            rectangles.append((key[0], top, key[1], bottom))

        for left, top, right, bottom in rectangles:
            self.show_region(left, top, image.crop((left, top, right, bottom)))

        return len(rectangles)

    def clear(self, colour="black"):
        """Fill the screen with a PIL colour name or an (R, G, B) tuple."""
        self.show(Image.new("RGB", (self.width, self.height), colour))

    def image(self, filename):
        """Display a PNG, JPEG, or other image supported by Pillow."""
        with Image.open(filename) as picture:
            self.show(picture)

    def new_image(self, colour="black"):
        """Create a PIL canvas at the current display resolution."""
        return Image.new("RGB", (self.width, self.height), colour)

    def draw(self, image):
        """Get a PIL ImageDraw object for drawing onto an image canvas."""
        return ImageDraw.Draw(image)

    def text(self, x, y, message, colour="white", font=None):
        """Clear the screen and display one line of text."""
        frame = self.new_image("black")
        painter = ImageDraw.Draw(frame)
        painter.text((x, y), str(message), fill=colour,
                     font=font or ImageFont.load_default())
        self.show(frame)

    def close(self):
        if not self._closed:
            self.spi.close()
            lgpio.gpiochip_close(self.gpio)
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

