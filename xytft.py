#!/usr/bin/env python3
"""
XYTFT-2.0'-SLCM ST7789V2 driver for Raspberry Pis.

Display:
    Controller: ST7789V2
    Resolution: 320 x 240 (landscape)
    Colour: RGB666 (18-bit)

Known-good wiring: CS GPIO8, MOSI GPIO10, SCLK GPIO11,
DC GPIO25, RESET GPIO27. Verified landscape is 320x240 at 32 MHz.
Requires: python3-spidev, python3-lgpio, python3-pil.

You user needs to belong to gpio,spi groups
(i.e. sudo usermod -aG gpio,spi $USER)

This driver was written by chatgpt using c++ code it analysed from the Chinese seller.
Be careful with your wiring, it is very sensitive


LCD pin	Wire colour	Raspberry Pi connection	Physical pin
VCC	        🔴 Red	  3.3V	                    1
GND	        ⚫ Black	 GND                       6
SCL	        🟡 Yellow GPIO11 / SPI0 SCLK        23
SDA	        🟢 Green  GPIO10 / SPI0 MOSI        19
CS	        🔵 Blue	  GPIO8 / SPI0 CE0	        24
DC	        ⚪ White	 GPIO25	                   22
RST	        🟠 Orange GPIO27	                13
BL	        🟣 Purple GPIO24                    18

Requirements:
    python3-spidev
    python3-lgpio
    python3-pil
"""

import time
import spidev
import lgpio
from io import BytesIO

from PIL import Image, ImageChops, ImageDraw, ImageFont

class Display:

    DC = 25
    RST = 27
    BL = 24  # BCM GPIO24, physical pin 18

    SPI_BUS = 0
    SPI_DEVICE = 0
    SPI_SPEED_HZ = 32_000_000

    _ROTATIONS = {
        0:   (0x60, 320, 240),
        90:  (0x00, 240, 320),
        180: (0xA0, 320, 240),
        270: (0xC0, 240, 320),
    }

    def __init__(self, spi_speed_hz=SPI_SPEED_HZ):

        self.width = 320
        self.height = 240
        self.rotation = 0

        self._closed = False
        self._initialized = False
        self._last_frame = None

        self.gpio = lgpio.gpiochip_open(0)

        try:
            lgpio.gpio_claim_output(self.gpio, self.DC, 1)
            lgpio.gpio_claim_output(self.gpio, self.RST, 1)

            self.spi = spidev.SpiDev()
            self.spi.open(self.SPI_BUS, self.SPI_DEVICE)

            self.spi.mode = 0
            self.spi.max_speed_hz = int(spi_speed_hz)
            self.spi.bits_per_word = 8
            lgpio.gpio_claim_output(self.gpio, self.BL, 0)

        except Exception:
            if hasattr(self, "spi"):
                self.spi.close()

            lgpio.gpiochip_close(self.gpio)
            self._closed = True
            raise

    # --------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------

    def init(self):
        """Initialize the ST7789V2 display."""

        if self._closed:
            raise RuntimeError("Display is closed")

        self._initialize()
        self._initialized = True

        self.clear("black")
        lgpio.gpio_write(self.gpio, self.BL, 1)

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

        # Sleep out
        self._command(0x11)
        time.sleep(0.12)

        # Column address
        self._command(0x2A)
        self._data([0x00, 0x00, 0x00, 0xEF])

        # Row address
        self._command(0x2B)
        self._data([0x00, 0x28, 0x01, 0x17])

        # Porch setting
        self._command(0xB2)
        self._data([0x0C, 0x0C, 0x00, 0x33, 0x33])

        # Inversion control
        self._command(0x20)

        # Gate control
        self._command(0xB7)
        self._data([0x56])

        # VCOM setting
        self._command(0xBB)
        self._data([0x18])

        # LCM control
        self._command(0xC0)
        self._data([0x2C])

        # VDV and VRH command enable
        self._command(0xC2)
        self._data([0x01])

        # VRH set
        self._command(0xC3)
        self._data([0x1F])

        # VDV set
        self._command(0xC4)
        self._data([0x20])

        # Frame rate control
        self._command(0xC6)
        self._data([0x0F])

        # Power control
        self._command(0xD0)
        self._data([0xA6, 0xA1])

        # Positive gamma
        gamma = [
            0xD0, 0x0D, 0x14, 0x0B,
            0x0B, 0x07, 0x3A, 0x44,
            0x50, 0x08, 0x13, 0x13,
            0x2D, 0x32
        ]

        self._command(0xE0)
        self._data(gamma)

        # Negative gamma
        self._command(0xE1)
        self._data(gamma)

        # Memory access control
        self._command(0x36)
        self._data([0x60])

        # RGB666 - 18-bit colour
        self._command(0x3A)
        self._data([0x66])

        # Vendor-specific setting
        self._command(0xE7)
        self._data([0x00])

        # Display inversion ON
        self._command(0x21)

        # Display ON
        self._command(0x29)

        time.sleep(0.05)

    # --------------------------------------------------
    # ROTATION
    # --------------------------------------------------

    def set_rotation(self, degrees):

        if self._closed:
            raise RuntimeError("Display is closed")

        if degrees not in self._ROTATIONS:
            raise ValueError(
                "Rotation must be 0, 90, 180 or 270"
            )

        madctl, self.width, self.height = (
            self._ROTATIONS[degrees]
        )

        self.rotation = degrees

        self._command(0x36)
        self._data([madctl])

        self._last_frame = None

    # --------------------------------------------------
    # DISPLAY WINDOW
    # --------------------------------------------------

    def _set_window(self):

        self._command(0x2A)

        self._data([
            0,
            0,
            (self.width - 1) >> 8,
            (self.width - 1) & 0xFF
        ])

        self._command(0x2B)

        self._data([
            0,
            0,
            (self.height - 1) >> 8,
            (self.height - 1) & 0xFF
        ])

    # --------------------------------------------------
    # DISPLAY IMAGE
    # --------------------------------------------------

    def show(self, image):
        """Display a PIL image."""

        if self._closed:
            raise RuntimeError("Display is closed")

        image = image.convert("RGB")

        if image.size != (self.width, self.height):

            image = image.resize(
                (self.width, self.height),
                Image.Resampling.LANCZOS
            )

        # RGB666: retain the upper six bits per channel.
        pixels = bytearray(image.tobytes())

        for i in range(len(pixels)):
            pixels[i] &= 0xFC

        self._set_window()

        self._command(0x2C)

        lgpio.gpio_write(self.gpio, self.DC, 1)

        # Send data in manageable SPI chunks.
        chunk_bytes = 3072

        for offset in range(0, len(pixels), chunk_bytes):

            self.spi.writebytes2(
                pixels[offset:offset + chunk_bytes]
            )

        self._last_frame = image.copy()

    def ShowImage(self, image_buffer):
        """
        Display an image supplied as a buffer.

        Accepts:
          - JPEG/PNG/etc. encoded bytes, bytearray or memoryview
          - io.BytesIO or another seekable file-like object
          - A Pillow Image object

        The image is converted to RGB and resized by show() if necessary.
        """
        if self._closed:
            raise RuntimeError("Display is closed")

        if isinstance(image_buffer, Image.Image):
            image = image_buffer.copy()

        elif isinstance(image_buffer, (bytes, bytearray, memoryview)):
            with Image.open(BytesIO(bytes(image_buffer))) as decoded:
                decoded.load()
                image = decoded.convert("RGB")

        elif hasattr(image_buffer, "read"):
            # Allow a reusable BytesIO/file-like buffer.
            if hasattr(image_buffer, "seek"):
                image_buffer.seek(0)

            with Image.open(image_buffer) as decoded:
                decoded.load()
                image = decoded.convert("RGB")

        else:
            raise TypeError(
                "image_buffer must be encoded image bytes, a file-like "
                "buffer, or a PIL Image"
            )

        self.show(image)

    # --------------------------------------------------
    # PARTIAL IMAGE UPDATE
    # --------------------------------------------------

    def show_region(self, x, y, image):
        """Update a rectangular region of the display."""

        if self._closed:
            raise RuntimeError("Display is closed")

        image = image.convert("RGB")

        x = int(x)
        y = int(y)

        left = max(0, x)
        top = max(0, y)

        right = min(self.width, x + image.width)
        bottom = min(self.height, y + image.height)

        if left >= right or top >= bottom:
            return

        crop = image.crop((
            left - x,
            top - y,
            right - x,
            bottom - y
        ))

        pixels = bytearray(crop.tobytes())

        for i in range(len(pixels)):
            pixels[i] &= 0xFC

        self._command(0x2A)

        self._data([
            left >> 8,
            left & 0xFF,
            (right - 1) >> 8,
            (right - 1) & 0xFF
        ])

        self._command(0x2B)

        self._data([
            top >> 8,
            top & 0xFF,
            (bottom - 1) >> 8,
            (bottom - 1) & 0xFF
        ])

        self._command(0x2C)

        lgpio.gpio_write(self.gpio, self.DC, 1)

        chunk_bytes = 3072

        for offset in range(0, len(pixels), chunk_bytes):

            self.spi.writebytes2(
                pixels[offset:offset + chunk_bytes]
            )

        if self._last_frame is not None:

            self._last_frame.paste(crop, (left, top))

    # --------------------------------------------------
    # UPDATE CHANGED AREAS ONLY
    # --------------------------------------------------

    def show_changed(self, image, tile_size=16):
        """Send only image tiles that have changed."""

        if self._closed:
            raise RuntimeError("Display is closed")

        if int(tile_size) < 1:
            raise ValueError("tile_size must be at least 1")

        tile_size = int(tile_size)

        image = image.convert("RGB")

        if image.size != (self.width, self.height):

            image = image.resize(
                (self.width, self.height),
                Image.Resampling.LANCZOS
            )

        if self._last_frame is None:

            self.show(image)
            return 1

        difference = ImageChops.difference(
            image,
            self._last_frame
        )

        row_runs = []

        for top in range(0, self.height, tile_size):

            bottom = min(top + tile_size, self.height)

            runs = []
            run_start = None

            for left in range(0, self.width, tile_size):

                right = min(left + tile_size, self.width)

                changed = difference.crop(
                    (left, top, right, bottom)
                ).getbbox()

                if changed and run_start is None:
                    run_start = left

                elif not changed and run_start is not None:

                    runs.append((
                        run_start,
                        top,
                        left,
                        bottom
                    ))

                    run_start = None

            if run_start is not None:

                runs.append((
                    run_start,
                    top,
                    self.width,
                    bottom
                ))

            row_runs.append(runs)

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

                    rectangles.append((
                        key[0],
                        old_top,
                        key[1],
                        old_bottom
                    ))

            active = current

        for key, (top, bottom) in active.items():

            rectangles.append((
                key[0],
                top,
                key[1],
                bottom
            ))

        for left, top, right, bottom in rectangles:

            self.show_region(
                left,
                top,
                image.crop((left, top, right, bottom))
            )

        return len(rectangles)

    # --------------------------------------------------
    # CLEAR DISPLAY
    # --------------------------------------------------

    def clear(self, colour="black"):
        """Fill the entire display with a colour."""

        self.show(
            Image.new(
                "RGB",
                (self.width, self.height),
                colour
            )
        )

    # --------------------------------------------------
    # DISPLAY IMAGE FILE
    # --------------------------------------------------

    def image(self, filename):
        """Display an image file supported by Pillow."""

        with Image.open(filename) as picture:
            self.show(picture)

    # --------------------------------------------------
    # CREATE IMAGE CANVAS
    # --------------------------------------------------

    def new_image(self, colour="black"):

        return Image.new(
            "RGB",
            (self.width, self.height),
            colour
        )

    # --------------------------------------------------
    # DRAWING
    # --------------------------------------------------

    def draw(self, image):

        return ImageDraw.Draw(image)

    def text(
        self,
        x,
        y,
        message,
        colour="white",
        font=None
    ):
        """Clear the display and draw a text message."""

        frame = self.new_image("black")

        painter = ImageDraw.Draw(frame)

        painter.text(
            (x, y),
            str(message),
            fill=colour,
            font=font or ImageFont.load_default()
        )

        self.show(frame)

    # --------------------------------------------------
    # CLOSE DISPLAY
    # --------------------------------------------------

    def close(self):
        """Turn off the backlight and release SPI/GPIO resources."""
        if self._closed:
            return

        try:
            lgpio.gpio_write(self.gpio, self.BL, 0)
        except Exception:
            pass

        try:
            self.spi.close()
        except Exception:
            pass

        try:
            lgpio.gpiochip_close(self.gpio)
        except Exception:
            pass

        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
