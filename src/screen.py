"""Manage screen content
"""

# flake8: noqa: F811
# flake8: noqa: W0201 attribute-defined-outside-init
# pylint: disable=invalid-name
# pylint: disable=attribute-defined-outside-init

import logging
import os
from dataclasses import dataclass, asdict
from typing import (List, Tuple, Dict, cast, )
from PIL import Image, ImageFont, ImageDraw
import requests

from .constants import (COROS, APP_CONTEXT, RPI, DSCREEN)
from .config import app_config
from .channel_manager import read_file
from .jrr_converter import image_resize
# from .messages import MsgScreenUpdate

# ------------------------------------------------------------------
# Module state
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Display driver

# from . import tft_ili9486
# driver = tft_ili9486.TFT_DRIVER(
#     dc=RPI.ILI9486.DC_PIN,
#     spi_bus=RPI.ILI9486.SPI_BUS,
#     spi_device=RPI.ILI9486.SPI_DEVICE,
#     rst=RPI.ILI9486.RST_PIN, )

ALPHA_OPAQUE = 255
ALPHA_INVISIBLE = 0
BLACK = 0
WHITE = 255
ALPHA_VALUE = ALPHA_INVISIBLE
COLOR_BLACK = (BLACK, BLACK, BLACK, ALPHA_VALUE)   # "black"
COLOR_RED = (255, 0, 0, ALPHA_OPAQUE)              # "red
COLOR_WHITE = (WHITE, WHITE, WHITE, ALPHA_VALUE)   # "white"
COLOR_BACKGROUND = COLOR_WHITE


# ------------------------------------------------------------------
# Screen configuration

LINE_SPACING = 30

DISPLAY_HEIGHT = RPI.ILI9486.HEIGHT

IMAGE_MODE = "RGB"
DEFAULT_FONT_SIZE = 25
CLOCK_FONT_SIZE = 48
COL0 = 0
COL1 = 25
COL2 = 150
# COL_CLOCK=150
COL_CLOCK = 25
# COL3 = 420
COL_ICONS = 400  # COL3


ROW_CLOCK = 0
ROW1 = 2*LINE_SPACING
ROW2 = ROW1 + LINE_SPACING
ROW4 = DISPLAY_HEIGHT - 2*LINE_SPACING
ROW3 = ROW4 - 1*LINE_SPACING
ROW_INFO = DISPLAY_HEIGHT - LINE_SPACING
FONT_DEF = "Font.ttc"         # file name for font definitions
BUTTON_SPACING = 3

# overlay stream icons with config screen
ROW_STREAM_ICON = 75
COL_STREAM_ICON = 200
OVERLAY_SIZE = (COL_STREAM_ICON+50, COL_STREAM_ICON)

# Adjust config title with btn1-long
ROW_CONFIG_TITLE = ROW_STREAM_ICON + BUTTON_SPACING - ROW1

# ------------------------------------------------------------------
# Dataclasses


@dataclass
class ScreenRoot:
    """Collect common methods here (if any)"""


@dataclass
class ScreenEntry(ScreenRoot):
    """Content of entry rendered on screen image.

    :name: uniquely identifies  screen entry

    :xy: pixel location '(x,y)' screen image .

    """

    name: str                          # mandatory unique name on screen
    x: int                             # x-axis location in pixels on screen
    y: int                             # y-axis location in pixels on screen
    active: bool = True

    # ------------------------------------------------------------------
    # Property setters
    # @property
    # def active(self) -> bool | None:
    #     """Read active."""
    #     if not hasattr(self, "_active"):
    #         return True
    #     return self._active

    # @active.setter
    # def active(self, active: bool):
    #     """Set active."""
    #     self._active = active

    @property
    def size(self):
        """Return (width, heigh, )."""
        raise NotImplementedError

    @property
    def to_text(self):
        """Return text representation - should implment in sub classes"""
        return f"{self.__class__.__name__} - not implemented"

    @property
    def bbox(self):
        """Return (left,upper,right,lower) rectangle."""
        raise NotImplementedError

    def cache_invalidate(self):
        """Clear any cache - in subclasses, if needed. Defult no action"""
        return

    def render_to_canvas(self, canvas: Image.Image) -> Image.Image:
        """Render content to canvas."""
        raise NotImplementedError(
            f"render_to_canvas - not implemented for '{self.__class__.__name__}'")


@dataclass
class ScreenEntryTxt(ScreenEntry):
    """'text' -string using 'font' on 'Screen' in position '(x,y)'."""

    text: str = ""                                  # Text to display
    # Max number of characater (alt for text_widht)
    text_len: int = 0
    # text_width: int | None = None                   # pixels for text  default hvalue (alt for text_len)
    font_size: int = DEFAULT_FONT_SIZE              # font_size w. default hvalue
    stroke_width: int = 0                           # in draw (bold when >0)
    anchor: str = "la"                              # left ascender
    _font: ImageFont.ImageFont | None = None        # Cached font

    # ----------
    # props

    @property
    def to_text(self):
        """Return text representation - should implment in sub classes"""
        return f"{self.text}"

    @property
    def font(self):
        """Cache font for of 'font_size'."""
        if self._font is None:
            self._font = ImageFont.truetype(
                os.path.join(app_config.pic_directory, FONT_DEF),
                self.font_size)
        return self._font

    # ------------------------------------------------------------------
    # helpers

    def anchor_2_pos(self, bbox: List) -> Tuple[int, int]:
        # anchor maps text position
        anchor_2_pos = {
            "la": (self.x, self.y),            # left top
            "ma": (int(self.x + (bbox[2] - bbox[0])/2), self.y),
            "ra": (bbox[2], self.y),
        }
        try:
            pos = anchor_2_pos[self.anchor]
        except KeyError as e:
            msg = f"Unsupported {self.anchor=}, support only for {[k for k in anchor_2_pos.keys()]}"
            logger.error("render_to_canvas: msg='%s'", msg)
            e.add_note(msg)
            raise

        return pos

    def bbox(self, draw: ImageDraw.Draw):
        bbox = draw.textbbox(
            (self.x, self.y),
            "X" * self.text_len,
            font=self.font,
        )
        return bbox

    # ------------------------------------------------------------------
    # render_to_canvas

    def render_to_canvas(self, canvas: Image.Image) -> Image.Image:
        """Update canvas with content for screen entry: in my case
        w. rendered'text')."""
        draw = ImageDraw.Draw(canvas)

        bbox = self.bbox(draw)

        # Create background to hide prev value
        draw.rectangle(bbox, fill=COLOR_BACKGROUND)

        pos = self.anchor_2_pos(bbox)

        logger.debug(
            "ScreenEntryTxt: xy=(%s,%s), pos=%s, anchor=%s, bbox=%s, font_size=%s, text_len=%s",
            self.x, self.y, pos, self.anchor, bbox, self.font_size, self.text_len)
        draw.text(
            pos,
            self.text,
            font=self.font,
            stroke_width=self.stroke_width,
            stroke_fill=COLOR_BLACK if self.stroke_width > 0 else None,
            anchor=self.anchor,
            fill=True,
        )
        return canvas


class ScreenEntryMultilineTxt(ScreenEntryTxt):
    def render_to_canvas(self, canvas: Image.Image) -> Image.Image:
        """Update canvas with content for screen entry: in my case
        w. rendered'text')."""
        draw = ImageDraw.Draw(canvas)

        bbox = draw.textbbox(
            (self.x, self.y),
            "X" * self.text_len,
            font=self.font,
        )
        # Create background to hide prev value
        draw.rectangle(bbox, fill=COLOR_BACKGROUND)

        pos = self.anchor_2_pos(bbox)

        logger.debug(
            "ScreenEntryTxt: xy=(%s,%s), pos=%s, anchor=%s, bbox=%s, font_size=%s, text_len=%s",
            self.x, self.y, pos, self.anchor, bbox, self.font_size, self.text_len)

        draw.text(
            pos,
            self.text,
            font=self.font,
            stroke_width=self.stroke_width,
            stroke_fill=COLOR_BLACK if self.stroke_width > 0 else None,
            anchor=self.anchor,
            fill=True,
        )
        return canvas


@dataclass
class ScreenEntryClock(ScreenEntryTxt):
    """Text with clock."""


@dataclass
class ScreenEntryInfo(ScreenEntryTxt):
    """Text for info line."""


@dataclass
class ScreenEntryImageBase(ScreenEntry):
    """Image screen entry on 'Screen'.

    Image drawn

    """
    # ------------------------------------------------------------------
    # Screen Entry representation (text/image rendering)

    @property
    def to_text(self):
        """Return text representation"""
        raise NotImplementedError("Should be overridden")

    @property
    def img(self) -> Image.Image:
        """
        Absstract image class
        """
        raise NotImplementedError("Should be overridden")

    def render_to_canvas(self, canvas: Image.Image) -> Image.Image:
        """Return 'Image' -object pasted to canvas."""
        img = self.img
        if img is not None:
            canvas.paste(img, (self.x, self.y))
        return canvas


@dataclass
class ScreenEntryImageFrame(ScreenEntryImageBase):
    """Image screen entry on 'Screen'.

    Borders for image.
    """

    width: int = -1                     # relative to self.x
    height: int = -1                    # relative to self.y
    line_width: int = 1                 # border line width in pixels

    @property
    def borders(self) -> List:
        origin = (0, 0)
        return [origin, self.size]

    @property
    def size(self) -> Tuple[int, int]:
        """Return (width, height)."""
        return (self.width, self.height)

    @property
    def to_text(self) -> str:
        """Return text representation"""
        return f"{self.name=}: {self.borders}, {self.line_width=}"

    @property
    def img(self) -> Image.Image:
        """
        Return rectangle image
        """
        image_mode = IMAGE_MODE
        logger.debug(
            "ScreenEntryImageFrame.img: self.size='%s', self.borders='%s'", self.size, self.borders)
        img = Image.new(image_mode, self.size)
        img1 = ImageDraw.Draw(img)
        img1.rectangle(self.borders,
                       fill=COLOR_BACKGROUND,
                       outline=COLOR_BLACK,
                       width=self.line_width)
        return img


@dataclass
class ScreenEntryImage(ScreenEntryImageBase):
    """Image screen entry on 'Screen'.

    Caches image in 'imagepath'

    """

    # path to image, empty string clears the image
    imagepath: str | None = None
    width: int | None = None                # resize width
    height: int | None = None
    volatile: bool = False                  # True not cached, may not exist

    # ------------------------------------------------------------------
    # Cached image

    @property
    def size(self) -> Tuple[int, int]:
        """Return (width, height)."""
        return (self.width if self.width is not None else 0,
                self.height if self.height is not None else 0)

    def cache_invalidate(self):
        """Clear/invalidate cached 'imagepath'."""
        self._img = None

    def maybe_resize(self, ):
        """Resize if both width and height given."""
        if self.width is None or self.height is None:
            return

        logger.info("maybe_resize: self.width='%s', self.height=%s",
                    self.width, self.height)
        self._img = image_resize(
            self._img, width=self.width, height=self.height)

    @property
    def _is_remote(self) -> bool:
        if self.imagepath is None:
            return False
        return (self.imagepath.startswith("http://") or
                self.imagepath.startswith("https://"))

    @property
    def _local_file(self) -> str:
        if self.imagepath is None:
            raise EnvironmentError("Imagepath None")
        if self.imagepath.startswith("file://"):
            return self.imagepath[7:]  # Remove 'file://' prefix
        return self.imagepath

    @ property
    def img(self) -> Image.Image | None:
        """Cached image for 'imagepath'.

        @see 'cache_invalidate' for cache invalidation.
        """
        if self.imagepath is None:
            return None

        if (not hasattr(self, "_img") or self._img is None or
                self.volatile):
            logger.debug(
                "ScreenEntryImage.img: read self.imagepath=%s, volatile=%s",
                self.imagepath, self.volatile)
            # if self.imagepath is not None and os.path.isfile(self.imagepath):
            if self.imagepath == "":
                self._img = Image.new(
                    IMAGE_MODE,
                    size=self.size, color=COLOR_BACKGROUND)
            elif self.imagepath is not None:

                try:
                    if self._is_remote:
                        self._img = Image.open(
                            requests.get(self.imagepath, stream=True, timeout=10).raw)
                    else:
                        self._img = Image.open(self._local_file)
                    self.maybe_resize()
                except FileNotFoundError as e:
                    # Not an error for volation
                    if self.volatile:
                        logger.warning("img: Error=%s for imagepath='%s'",
                                       e, self.imagepath)
                        self._img = None
                    else:
                        raise
        return self._img

    # ------------------------------------------------------------------
    # Screen Entry representation (text/image rendering)

    @ property
    def to_text(self):
        """Return text representation"""
        return f"{self.imagepath}"


@ dataclass
class ScreenEntryImageIconsBase(ScreenEntryImage):
    """Base class for icon sprites.

    Icons are fixed size sprites combined together in 'imagepath'.

    """
    vertical: bool = False      # verfical/horizon stack
    spacing: int = 0            # number of pixes between icons

    @ property
    def icon_count(self):
        """Return number of icons on screen entry. """
        # fixed value 'network' and 'streaming'
        raise NotImplementedError(
            f"not implemented for '{self.__class__.__name__}'")

    def _icon_indexes(self) -> List[int]:
        raise NotImplementedError(
            f"not implemented for '{self.__class__.__name__}'")

    @property
    def size(self):
        """Return (width, height).

        - (icon_count*icon_size, icon_size) for horizontal (not vertical)
        - (icon_size, icon_count*icon_size, ) for vertical
        """

        ret = (
            self.icon_count*app_config.sprite_icon_size +
            (self.icon_count-1)*self.spacing,
            app_config.sprite_icon_size
        )
        if self.vertical:
            ret = (ret[1], ret[0])
        return ret

    @property
    def img(self) -> Image.Image:
        """Create display sprite refracing object state (network, streaming).

        Icons are stacked vertically/horizontally

        """

        # Cached image from sprite file
        sprite_icons = super().img

        # Facts for calculation
        icon_indexes = self._icon_indexes()
        size = self.size
        icon_size = app_config.sprite_icon_size

        logger.info("ScreenEntryImageIcons: size: %s, indexes=%s, iconsize: %s",
                    size, icon_indexes, icon_size)
        img = Image.new(IMAGE_MODE, size, COLOR_BACKGROUND)

        # put 'icon_index' from imagepath to 'index' in sprite
        for index, icon_index in enumerate(icon_indexes):
            icon_bbox = (icon_index*icon_size, 0,
                         (icon_index+1)*icon_size, icon_size)
            chosen_icon = sprite_icons.crop(icon_bbox)
            xy = (index*(icon_size + self.spacing), 0)
            if self.vertical:
                xy = (xy[1], xy[0])
            img.paste(chosen_icon, xy)

        return img


@dataclass
class ScreenEntryStatusDashDot(ScreenEntryImageIconsBase):
    """Screen entry for keyboard help

    """

    @property
    def icon_count(self):
        """Two icons dash and dot. """
        # fixed value 'network' and 'streaming'
        return 2

    def _icon_indexes(self) -> List[int]:
        """Return list of indexes to choose from icon sprite for display.

        In my case icon-sprite.png contains dot in position 4 and dash
        in position 5.

        """
        dot_index = 4
        dash_index = 5
        return [dot_index, dash_index]

    @property
    def to_text(self):
        """Return text representation"""
        return f"Icons dash and dot"


@dataclass
class ScreenEntryStatusIcons(ScreenEntryImageIconsBase):
    """Screen entry for network, streaming and keyboard status.

    """

    network: bool = False                  # Network status ok/error
    streaming: bool = False                # Streaming true/false
    keyboard: bool = False                 # Keyboard connected

    @property
    def icon_count(self):
        """Return number of icons on screen entry. """
        # fixed value 'network' and 'streaming'
        return 3

    def _icon_indexes(self) -> List[int]:
        """Return list of indexes to choose from icon sprite for display."""
        network_icon_index = 0 if self.network else 1
        streaming_icon_index = 2 if self.streaming else 3
        keyboard_icon_index = 6 if self.keyboard else 7
        return [network_icon_index, streaming_icon_index, keyboard_icon_index]

    @property
    def to_text(self):
        """Return text representation"""
        return f"{self.network=}, {self.streaming=}, {self.keyboard=}"


# ------------------------------------------------------------------
# Screen layout

# map layout name to Dictionary mapping screen entry name to
# List[constructor:class, xy position:dict]
# SCREEN_LAYOUTS: Dict = {}


# ------------------------------------------------------------------
# Screen content


class Screen(ScreenRoot):
    """Manage screen content and render content to an image.

    :screen_entries: screen_content, managed in 'add_or_update_entry'

    :_img: cached image, updated in 'update' and 'update_partial
    methods'.

    """

    def __init__(self, size: Tuple[int, int],
                 layout_name: str = APP_CONTEXT.SCREEN_LAYOUTS.STREAMING,
                 layout: Dict | None = None,
                 backgroud_color=None,
                 ):
        """

        :layout_name: initial layout overrides laytout - if given

        """

        # data buffer
        self.screen_entries: List[ScreenEntry] = []

        # size of display
        self.size = size

        # Screen layout layout_name overrides
        self.layout = layout
        if layout_name is not None:
            self.layout = SCREEN_LAYOUTS[layout_name]

        # background color for canvas
        self.backgroud_color = backgroud_color

        # Cached image - initially None
        self.invalidate_image_cache()

    # ------------------------------------------------------------------
    # Layout configuration

    @property
    def current_layout(self) -> Dict:
        """Current layot mapping screen entry name to tuple
        (constructor class, entry default properties).

        """
        return self.layout

    # ------------------------------------------------------------------
    # Some helpers
    def named_screen_entry(
            self, name: str,
            screen_entries: List[ScreenEntry] | None = None
    ) -> ScreenEntry | None:
        """Recursively search for screen entry by name.

        :name: base screen entry name or path screen containerEntry.baseEntry.

        :screen_entries: List to search from (default my
        self.screen_entries)

        """

        if screen_entries is None:
            screen_entries = self.screen_entries

        attribute_path = name.split(sep=".", maxsplit=1)
        base_name = attribute_path[0]

        g_existing_screen_entry = (
            se for se in screen_entries if se.name == base_name)
        try:
            screen_entry: ScreenEntry | None = next(g_existing_screen_entry)

            if len(attribute_path) == 1:
                return screen_entry

            # recursion
            container_entry = cast(ScreenEntryContainer, screen_entry)
            screen_entry = self.named_screen_entry(
                name=attribute_path[1],
                screen_entries=container_entry.screen.screen_entries)
            return screen_entry

        except StopIteration:
            return None

        return screen_entry

    # ------------------------------------------------------------------
    # Image cache to put on display

    def invalidate_image_cache(self):
        """Invalidate image Buffer. Next screen update (full/partial)
        builds from scratch.

        """
        self._img = None

    @property
    def img(self):
        """Return cached imaged (use update_full if cache invalid)"""
        if self._img is None:
            self._img = self._get_display_buffer()
        return self._img

    # ------------------------------------------------------------------
    # Build image cache (self.img) from screen data buffer
    # (screen_entries)

    def update_partial(self, name: str | None) -> Image.Image:
        """Partial update of cached image (self._img)."""

        # current (cached?/rebuilt) img canvas
        canvas = self.img
        # update part of canvas (and update cache)
        self._img = self._get_display_buffer(canvas=canvas, name=name)
        return self._img

    def update_full(self):
        """Return screen image using all 'screen_entries'."""
        self._img = self._get_display_buffer()
        return self._img

    def _get_display_buffer(
            self,
            canvas: Image.Image | None = None,
            name: str | None = None

    ) -> Image.Image:
        """Return image for rendering using data from active screen
        entries/named screen entry.

        :canvas: update to canvas, create empty canvas if None

        :name: update named screen entry if given (default update all
        screeen entries)

        """

        # Init empty canvas, if no canvas to update given
        if canvas is None:
            canvas = self.empty_image(
                color=self.backgroud_color,
                size=self.size
            )

        # Iterate all screen_entries/named screen entry
        g_screen_entries = (
            se for se in self.screen_entries
            if se.active and name is None or se.name == name)

        for screen_entry in g_screen_entries:
            logger.debug(
                "render to canvas screen_entry.name=%s: to_text=%s[%s]",
                screen_entry.name, screen_entry.to_text,
                type(screen_entry.to_text))
            canvas = screen_entry.render_to_canvas(canvas)

        return canvas

    # ------------------------------------------------------------------
    # Add/update content on screen data buffers (screen entry)

    def activate_entry(self, name: str, active: bool):
        """Set screen entry 'name' to 'active' state."""
        screen_entry = self.named_screen_entry(name)
        if screen_entry is not None:
            screen_entry.active = active

    def add_or_update_entry(self,
                            name: str,
                            entry_props: Dict,
                            ) -> bool:
        """Add/update screen entry 'name' with properties
        'message_props'.

        Create new screen entry using 'screen_layout', if 'name'
        missing from 'screen_entries'

        :name: of screen entry to create/update

        :entry_props: dictionary of properties for creating/updating
        screen entry. None values are ignored (ie. screen content is
        not changed.)

        :return: update_needed = entry changed/created

        """
        logger.debug(
            "add_or_update_entry: name='%s', entry_props=%s", name, entry_props)

        # Change True if display needs update
        update_needed = False

        # Generator to find existing screen entry
        existing_screen_entry = self.named_screen_entry(name)

        def update_existing_entry(existing_screen_entry, entry_props) -> bool:
            update_needed = False
            for k, v in entry_props.items():
                old_v = getattr(existing_screen_entry, k)
                if old_v != v and v is not None:
                    # existing screen entry modified
                    update_needed = True
                    existing_screen_entry.cache_invalidate()
                    setattr(existing_screen_entry, k, v)
            return update_needed

        if existing_screen_entry is not None:
            # existing_screen_entry found
            logger.debug(
                "existing_entry '%s' found, set old %s --> new %s len-ent: %s",
                existing_screen_entry.name,
                asdict(existing_screen_entry),
                entry_props,
                len(self.screen_entries),
            )

            # update 'existing_screen_entry' with 'entry_props'
            update_needed = update_existing_entry(
                existing_screen_entry=existing_screen_entry,
                entry_props=entry_props)

        else:
            # Need to create new screen entry
            update_needed = True

            try:
                screen_entry_class, screen_entry_defaults = self.current_layout[name]
            except KeyError as ex:
                msg = f"{name=} not in {self.current_layout.keys()}"
                logger.warning(msg)
                ex.add_note(msg)
                raise

            # Create initial entry
            screen_entry_props = screen_entry_defaults | {
                "name": name
            }
            logger.debug(
                "new screen.entry: name: %s, msg_props: %s, len-entries: %s, screen_entry_class: %s",
                name,
                screen_entry_props,
                len(self.screen_entries),
                screen_entry_class,

            )
            try:
                created_screen_entry = screen_entry_class(**screen_entry_props)
            except Exception as ex:
                msg = f"{ex}: when creating {screen_entry_class=} for {screen_entry_props}"
                logger.error(msg)
                ex.add_note(msg)
                raise

            # Put requested proprties on screen entry
            self.screen_entries.append(created_screen_entry)
            update_existing_entry(
                existing_screen_entry=created_screen_entry,
                entry_props=entry_props)

        # finally - return need for update
        logger.debug("add_or_update_entry: update_needed='%s'", update_needed)
        return update_needed

    def clear(self):
        """Clear content (='screen_entries') and 'invalidate_image_cache'."""
        self.screen_entries = []
        self.invalidate_image_cache()

    # ------------------------------------------------------------------
    # Base image

    def empty_image(self, color=None, size=None,
                    image_mode=IMAGE_MODE) -> Image.Image:
        """Return black&white of 'size'  in 'color'.

        :color: 255=white, 0=black

        :size: (width, height) (default self.size)

        :image_mode: Most likely RGB but maybe some use for RGBA or 1.

        """
        if size is None:
            size = self.size

        if color is None:
            color = COLOR_BACKGROUND

        img = Image.new(image_mode, size, color)
        return img

# ------------------------------------------------------------------
# Screen container


@dataclass
class ScreenEntryContainer(ScreenEntry):
    """Content for a sub-image  on 'Screen'"""

    def __init__(self,
                 name: str,
                 x: int,
                 y: int,
                 size: Tuple[int, int],
                 layout_name: str = None,
                 layout: Dict = None,
                 init: bool = True,
                 ):
        """Construct container screen entry with 'name' and in
        position 'xy', and 'size'. Content of conainer with 'layout'
        is rendered on canvas of 'size'.

        :init: True init empty screen_entries for layot
        """

        super().__init__(name=name, x=x, y=y)

        self.screen = Screen(size=size, layout_name=layout_name, layout=layout)
        if init:
            self.init_contained_entries()

    def init_contained_entries(self):
        """Add all 'screen_elements' defined in screen.layout """
        for name in self.screen.layout.keys():
            self.screen.add_or_update_entry(
                name=name,
                entry_props={}
            )

    # ------------------------------------------------------------------
    # Getter and setters (used in add_or_update_entry)

    def contained_entry(self, name: str) -> ScreenEntry | None:
        """Return ScreenEntry with 'name' from 'screen.screen_entries'.


        :return: None if not found
        """
        g_screen_entry = (
            se for se in self.screen.screen_entries if se.name == name)
        try:
            ret = next(g_screen_entry)
        except StopIteration:
            ret = None
        return ret

    def __getattr__(self, name: str):
        try:
            # Try to access base attributes
            value = super().__getattribute__(name)
        except AttributeError:
            # No base attribute found --> access container attribute (container.name)
            attribute_path = name.split(sep=".")
            screen_entry = self.contained_entry(name=attribute_path[0])
            if screen_entry is None:
                value = None
            else:
                value = getattr(screen_entry, attribute_path[1])
        return value

    def __setattr__(self, name, value):
        attribute_path = name.split(sep=".")
        if len(attribute_path) == 1:
            # Set base attribute
            super().__setattr__(name, value)
        else:
            # Set attribute in container
            screen_entry_name = attribute_path[0]
            screen_entry_prop = attribute_path[1]
            screen_entry = self.contained_entry(name=screen_entry_name)
            if screen_entry is None:
                # Create screen entry to container (and set value)
                entry_props = {
                    screen_entry_prop: value
                }
                logger.debug("update: screen_entry_name='%s', entry_props='%s'",
                             screen_entry_name, entry_props)
                self.screen.add_or_update_entry(
                    name=screen_entry_name, entry_props=entry_props)
            else:
                # set attribute in existing screen entry in a container
                setattr(screen_entry, screen_entry_prop, value)

    # ------------------------------------------------------------------
    # Cached image

    def cache_invalidate(self):
        """Clear/invalidate cached 'imagepath'."""
        self._img = None
        self.screen.invalidate_image_cache()

    @property
    def img(self) -> Image.Image:
        """Cached image for 'imagepath'.

        @see 'cache_invalidate' for cache invalidation.
        """
        if not hasattr(self, "_img") or self._img is None:
            self._img = self.screen.img
        return self._img

    # ------------------------------------------------------------------
    # Screen Entry representation (text/image rendering)

    def render_to_canvas(self, canvas: Image.Image) -> Image.Image:
        """Deletege rendering Render content to canvas."""
        canvas.paste(self.img, (self.x, self.y))
        return canvas

    # ------------------------------------------------------------------
    # Convinience

    def __repr__(self):
        child_repr = '\n'.join([repr(se) for se in self.screen.screen_entries])
        return f"Container: {super().__repr__()}\nContained: {child_repr}"


# ------------------------------------------------------------------
#


layout_base: Dict = {
    # Layout config common to all layouts
    #
    # Map screen entry name -> List[constructor:class, xy position:dict]
    # to List
    COROS.Screen.ENTRY_CLOCK: [ScreenEntryClock,
                               {"x": COL_CLOCK, "y": ROW_CLOCK,
                                "font_size": CLOCK_FONT_SIZE,
                                "text_len": 10,
                                }],

    COROS.Screen.ENTRY_SPRITE_ICONS: [
        ScreenEntryStatusIcons,
        {"x": COL_ICONS, "y": ROW_CLOCK, "vertical": False}],
    COROS.Screen.ENTRY_ICON_KEY1: [
        ScreenEntryStatusDashDot,
        {"x": COL0, "y": ROW1 + BUTTON_SPACING, "vertical": True, "spacing": 6}],
    COROS.Screen.ENTRY_ICON_KEY2: [
        ScreenEntryStatusDashDot,
        {"x": COL0, "y": ROW3 + BUTTON_SPACING, "vertical": True, "spacing": 6}],
    COROS.Screen.ENTRY_B1: [
        ScreenEntryTxt,
        {"x": COL1, "y": ROW1, "text_len": 7, }],    # button1
    COROS.Screen.ENTRY_B2: [
        ScreenEntryTxt,
        {"x": COL1, "y": ROW2, "text_len": 10, }],
    COROS.Screen.ENTRY_B3: [
        ScreenEntryTxt,
        {"x": COL1, "y": ROW3, "text_len": 10, }],
    COROS.Screen.ENTRY_B4: [
        ScreenEntryTxt,
        {"x": COL1, "y": ROW4, "text_len": 10, }],
    COROS.Screen.ENTRY_MSG_L1: [
        ScreenEntryInfo,
        {"x": COL2, "y": ROW_INFO, "text_len": 20, }],
    COROS.Screen.ENTRY_VERSION: [
        ScreenEntryInfo,
        {"x": COL1, "y": ROW_INFO, "text_len": 20, "font_size": 10,
         "text": "jrr-0.0.latest",
         }],

    # COROS.Screen.ENTRY_MSG_L2: [ScreenEntryInfo,
    #                             {"x": COL2, "y": ROW_INFO + LINE_SPACING, "text_len": 10, }],
}

# ------------------------------------------------------------------
# Configuration overlays (replacing)
_layout_config = {
    "line1": [ScreenEntryTxt,
              {"x": 0, "y": 0, "text_len": 7, }],
    "line2": [ScreenEntryTxt,
              {"x": 0, "y": 20, "text_len": 7, }],
}

_layout_config_menu = {

    # data content is rendered on top of frame
    "borders": [
        ScreenEntryImageFrame,
        {"x": 0, "y": 0, "width": OVERLAY_SIZE[0], "height": OVERLAY_SIZE[1],
         "line_width": 2}],

    DSCREEN.CONFIG_TITLE_OVERLAY.HEADER: [
        ScreenEntryTxt,
        {"x": 2, "y": ROW_CONFIG_TITLE, "text_len": 17,
         "font_size": 20, "text": "MENU", "stroke_width": 1,
         "anchor": "ma"}],


    DSCREEN.CONFIG_TITLE_OVERLAY.SUB_HEADER: [
        ScreenEntryTxt,
        {"x": 2, "y": ROW_CONFIG_TITLE + 25, "text_len": 17,
         "font_size": 20, "text": "MENU", "stroke_width": 1,
         "anchor": "ma"}],

    DSCREEN.QUESTION_OVERLAY.ICON:  [
        ScreenEntryImage,
        {"x": int((OVERLAY_SIZE[0]-100)/2), "y": LINE_SPACING*3,
         "width": int(OVERLAY_SIZE[0]/2), "height": int(OVERLAY_SIZE[1]/2),
         "imagepath": None, "volatile": True
         }],

}

_layout_wifi_entry = {
    DSCREEN.WIFI_OVERLAY.HEADER:  [
        ScreenEntryTxt,
        {"x": 0, "y": 0, "text_len": 7,
         "font_size": 20,
         "text": APP_CONTEXT.MENU.MENU_DO_CONFIG_WIFI,
         "stroke_width": 1}],
    DSCREEN.WIFI_OVERLAY.SSID+"-prompt":  [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING, "text_len": 7,
         "font_size": 20,
         "text": APP_CONTEXT.MENU.WIFI_SETUP_SCREEN.SSID_PROMPT,
         "stroke_width": 0}],
    DSCREEN.WIFI_OVERLAY.SSID:  [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING*2, "text_len": 7,
         "font_size": 20, "text": None, "stroke_width": 1}],
    DSCREEN.WIFI_OVERLAY.PASSWORD+"-prompt": [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING*3, "text_len": 7,
         "font_size": 20,
         "text": APP_CONTEXT.MENU.WIFI_SETUP_SCREEN.PASSWORD_PROMPT,
         "stroke_width": 0}],
    DSCREEN.WIFI_OVERLAY.PASSWORD: [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING*4, "text_len": 7,
         "font_size": 20, "text": None, "stroke_width": 1}],
}

_layout_error = {
    DSCREEN.ERROR_OVERLAY.ERROR:  [
        ScreenEntryTxt,
        {"x": 0, "y": 0, "text_len": 15,
         "font_size": 20, "anchor": "ma",
         "text": None, "stroke_width": 1}],

    DSCREEN.ERROR_OVERLAY.INSTRUCTIONS:  [
        ScreenEntryMultilineTxt,
        {"x": 0, "y": LINE_SPACING, "text_len": 30,
         "font_size": 13, "anchor": "la",
         "text": None, "stroke_width": 0}],

    DSCREEN.ERROR_OVERLAY.ICON:  [
        ScreenEntryImage,
        {"x": int((OVERLAY_SIZE[0]-100)/2), "y": LINE_SPACING*3,
         "volatile": True,
         "imagepath": os.path.join(APP_CONTEXT.APP_RESOURCES, "error-100.png"),
         }],

}

_layout_question = {
    DSCREEN.QUESTION_OVERLAY.TITLE:  [
        ScreenEntryTxt,
        {"x": 0, "y": 0, "text_len": 15,
         "font_size": 20, "anchor": "ma",
         "text": None, "stroke_width": 1}],

    DSCREEN.QUESTION_OVERLAY.QUESTION:  [
        ScreenEntryMultilineTxt,
        {"x": 0, "y": LINE_SPACING, "text_len": 30,
         "font_size": 13, "anchor": "la",
         "text": None, "stroke_width": 0}],

    DSCREEN.QUESTION_OVERLAY.ICON:  [
        ScreenEntryImage,
        {"x": int((OVERLAY_SIZE[0]-100)/2), "y": LINE_SPACING*3,
         "width": int(OVERLAY_SIZE[0]/2), "height": int(OVERLAY_SIZE[1]/2),
         "imagepath": None, "volatile": True
         }],
}

_layout_firware_info = {
    DSCREEN.FIRMWARE_OVERLAY.HEADER:  [
        ScreenEntryTxt,
        {"x": 0, "y": 0, "text_len": 15,
         "font_size": 20, "anchor": "ma",
         "text": None, "stroke_width": 1}],

    DSCREEN.FIRMWARE_OVERLAY.VERSION_TAG:  [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING, "text_len": 15,
         "font_size": 20, "anchor": "ma",
         "text": None, "stroke_width": 1}],

    DSCREEN.FIRMWARE_OVERLAY.NOTES:  [
        ScreenEntryMultilineTxt,
        {"x": 0, "y": 2*LINE_SPACING, "text_len": 30,
         "font_size": 10, "anchor": "la",
         "text": None, "stroke_width": 0}],
}

_layout_network_info = {

    "borders": [
        ScreenEntryImageFrame,
        {"x": 0, "y": 0, "width": OVERLAY_SIZE[0], "height": OVERLAY_SIZE[1],
         "line_width": 2}],

    DSCREEN.NETWORK_INFO_OVERLAY.TITLE: [
        ScreenEntryTxt,
        {"x": 2, "y": ROW_CONFIG_TITLE, "text_len": 17,
         "font_size": 20, "text": "MENU", "stroke_width": 1,
         "anchor": "ma"}],

    DSCREEN.NETWORK_INFO_OVERLAY.SUB_TITLE: [
        ScreenEntryTxt,
        {"x": 2, "y": ROW_CONFIG_TITLE + 25, "text_len": 17,
         "font_size": 20, "text": "MENU", "stroke_width": 1,
         "anchor": "ma"}],

    DSCREEN.NETWORK_INFO_OVERLAY.IP + "-label": [
        ScreenEntryTxt,
        {"x": 2, "y": ROW_CONFIG_TITLE + 25 + 2*LINE_SPACING, "text_len": 17,
         "font_size": 20, "text": "IP:", "stroke_width": 0,
         "anchor": "la"}],

    DSCREEN.NETWORK_INFO_OVERLAY.IP: [
        ScreenEntryTxt,
        {"x": 52, "y": ROW_CONFIG_TITLE + 25 + 2*LINE_SPACING, "text_len": 17,
         "font_size": 20, "text": None, "stroke_width": 1,
         "anchor": "la"}],

    DSCREEN.NETWORK_INFO_OVERLAY.SSID+"-label": [
        ScreenEntryTxt,
        {"x": 2, "y": ROW_CONFIG_TITLE + 25 + 3*LINE_SPACING, "text_len": 17,
         "font_size": 20, "text": "SSID:", "stroke_width": 0,
         "anchor": "la"}],

    DSCREEN.NETWORK_INFO_OVERLAY.SSID: [
        ScreenEntryTxt,
        {"x": 52, "y": ROW_CONFIG_TITLE + 25 + 3*LINE_SPACING, "text_len": 17,
         "font_size": 20, "text": None, "stroke_width": 1,
         "anchor": "la"}],

}


_layout_url_load = {
    DSCREEN.URL_LOAD_OVERLAY.TITLE:  [
        ScreenEntryTxt,
        {"x": 0, "y": 0, "text_len": 30,
         "font_size": 20,
         "text": APP_CONTEXT.MENU.WIFI_SETUP, "stroke_width": 1}],
    DSCREEN.URL_LOAD_OVERLAY.URL_BASE+"-prompt":  [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING, "text_len": 20,
         "font_size": 20, "text": "URL-base:", "stroke_width": 1}],
    DSCREEN.URL_LOAD_OVERLAY.URL_BASE:  [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING*2, "text_len": 20,
         "font_size": 20, "text": "", "stroke_width": 0}],
    DSCREEN.URL_LOAD_OVERLAY.YAML_FILE+"-prompt": [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING*3, "text_len": 7,
         "font_size": 20, "text": "yaml:", "stroke_width": 1}],
    DSCREEN.URL_LOAD_OVERLAY.YAML_FILE: [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING*4, "text_len": 7,
         "font_size": 20, "text": "yaml", "stroke_width": 0}],
}

_layout_firmware = {
    DSCREEN.FIRMWARE_OVERLAY.HEADER:  [
        ScreenEntryTxt,
        {"x": 0, "y": 0, "text_len": 30,
         "font_size": 20,
         "text": APP_CONTEXT.MENU.WIFI_SETUP, "stroke_width": 1}],
    DSCREEN.FIRMWARE_OVERLAY.VERSION_TAG+"-prompt":  [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING, "text_len": 20,
         "font_size": 20, "text": "Versio:", "stroke_width": 1}],
    DSCREEN.FIRMWARE_OVERLAY.VERSION_TAG:  [
        ScreenEntryTxt,
        {"x": 0, "y": LINE_SPACING*2, "text_len": 20,
         "font_size": 20, "text": "", "stroke_width": 0}],
}



# One of these is active at one time (= images override each other.)
# - This means that canvas sizes are equal (container size == stream icon size
# - xy -positions are the same
overlay_layouts: Dict = {

    COROS.Screen.ENTRY_STREAM_ICON: [
        ScreenEntryImage,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON}],
    COROS.Screen.ENTRY_CONFIG_TITLE:  [
        ScreenEntryContainer,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON,
         "size": OVERLAY_SIZE,
         "layout": _layout_config_menu,
         # "layout_name": APP_CONTEXT.SCREEN_LAYOUTS.CONFIGURATION_MENU,
         }],
    COROS.Screen.ENTRY_CONFIG:  [
        ScreenEntryContainer,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON,
         "size": OVERLAY_SIZE,
         "layout": _layout_config,
         # "layout_name": APP_CONTEXT.SCREEN_LAYOUTS.CONFIGURATION_CONTAINER,
         }],
    COROS.Screen.ENTRY_WIFI_OVL: [
        ScreenEntryContainer,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON,
         "size": OVERLAY_SIZE,
         "layout": _layout_wifi_entry,
         }],
    COROS.Screen.ENTRY_URL_LOAD_OVL: [
        ScreenEntryContainer,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON,
         "size": OVERLAY_SIZE,
         "layout": _layout_url_load,
         }],
    COROS.Screen.ENTRY_FIRMWARE1_OVL: [
        ScreenEntryContainer,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON,
         "size": OVERLAY_SIZE,
         "layout": _layout_firmware,
         }],
    COROS.Screen.ENTRY_ERROR_OVL: [
        ScreenEntryContainer,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON,
         "size": OVERLAY_SIZE,
         "layout": _layout_error,
         }],
    COROS.Screen.ENTRY_QUESTION_OVL: [
        ScreenEntryContainer,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON,
         "size": OVERLAY_SIZE,
         "layout": _layout_question,
         }],
    COROS.Screen.ENTRY_NETWORK_INFO_OVL: [
        ScreenEntryContainer,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON,
         "size": OVERLAY_SIZE,
         "layout": _layout_network_info,
         }],
    COROS.Screen.ENTRY_FIRMWARE2_OVL: [
        ScreenEntryContainer,
        {"x": COL_STREAM_ICON, "y": ROW_STREAM_ICON,
         "size": OVERLAY_SIZE,
         "layout": _layout_firware_info,
         }],
}  # overlay_layouts - dict


def overlay_names() -> List[str]:
    """Return overlay names."""
    return list(overlay_layouts.keys())


# map layout_name to List[constructor:class, constructor:dict]
SCREEN_LAYOUTS = {
    # Base display (with alternative_layouts)
    APP_CONTEXT.SCREEN_LAYOUTS.STREAMING: layout_base | overlay_layouts,

    # Container layout (for entering configuration )
    APP_CONTEXT.SCREEN_LAYOUTS.CONFIGURATION_CONTAINER: _layout_config,

    # Container layout (for choosin configuration)
    # APP_CONTEXT.SCREEN_LAYOUTS.CONFIGURATION_MENU: _layout_config_menu,

}
