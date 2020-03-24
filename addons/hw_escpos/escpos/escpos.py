# -*- coding: utf-8 -*-
import io
import base64
import math
import hashlib
import re
import traceback
import codecs
import xml.etree.ElementTree as ET

from PIL import Image

try:
    import jcconv
except ImportError:
    jcconv = None

try:
    import qrcode
except ImportError:
    qrcode = None

from escpos.escpos import Escpos as EscposCore
from escpos.constants import *
from escpos.exceptions import *


def utfstr(stuff):
    """ converts stuff to string and does without failing if stuff is a utf8 string """
    if isinstance(stuff, str):
        return stuff
    else:
        return str(stuff)


class StyleStack:
    """
    The stylestack is used by the xml receipt serializer to compute the active styles along the xml
    document. Styles are just xml attributes, there is no css mechanism. But the style applied by
    the attributes are inherited by deeper nodes.
    """

    def __init__(self):
        self.stack = []
        self.defaults = {  # default style values
            'align': 'left',
            'underline': 'off',
            'bold': 'off',
            'size': 'normal',
            'font': 'a',
            'width': 48,
            'indent': 0,
            'tabwidth': 2,
            'bullet': ' - ',
            'line-ratio': 0.5,
            'color': 'black',

            'value-decimals': 2,
            'value-symbol': '',
            'value-symbol-position': 'after',
            'value-autoint': 'off',
            'value-decimals-separator': '.',
            'value-thousands-separator': ',',
            'value-width': 0,

        }

        self.types = {  # attribute types, default is string and can be ommitted
            'width': 'int',
            'indent': 'int',
            'tabwidth': 'int',
            'line-ratio': 'float',
            'value-decimals': 'int',
            'value-width': 'int',
        }

        self.cmds = {
            # translation from styles to escpos commands
            # some style do not correspond to escpos command are used by
            # the serializer instead
            'align': {
                'left': TXT_ALIGN_LT,
                'right': TXT_ALIGN_RT,
                'center': TXT_ALIGN_CT,
                '_order': 1,
            },
            'underline': {
                'off': TXT_UNDERL_OFF,
                'on': TXT_UNDERL_ON,
                'double': TXT_UNDERL2_ON,
                # must be issued after 'size' command
                # because ESC ! resets ESC -
                '_order': 10,
            },
            'bold': {
                'off': TXT_BOLD_OFF,
                'on': TXT_BOLD_ON,
                # must be issued after 'size' command
                # because ESC ! resets ESC -
                '_order': 10,
            },
            'font': {
                'a': TXT_FONT_A,
                'b': TXT_FONT_B,
                # must be issued after 'size' command
                # because ESC ! resets ESC -
                '_order': 10,
            },
            'size': {
                'normal': TXT_NORMAL,
                'double-height': TXT_2HEIGHT,
                'double-width': TXT_2WIDTH,
                'double': TXT_4SQUARE,
                '_order': 1,
            },
            'color': {
                'black': TXT_COLOR_BLACK,
                'red': TXT_COLOR_RED,
                '_order': 1,
            },
        }

        self.push(self.defaults)

    def get(self, style):
        """ what's the value of a style at the current stack level"""
        level = len(self.stack) - 1
        while level >= 0:
            if style in self.stack[level]:
                return self.stack[level][style]
            else:
                level = level - 1
        return None

    def enforce_type(self, attr, val):
        """converts a value to the attribute's type"""
        if not attr in self.types:
            return utfstr(val)
        elif self.types[attr] == 'int':
            return int(float(val))
        elif self.types[attr] == 'float':
            return float(val)
        else:
            return utfstr(val)

    def push(self, style={}):
        """push a new level on the stack with a style dictionnary containing style:value pairs"""
        _style = {}
        for attr in style:
            if attr in self.cmds and not style[attr] in self.cmds[attr]:
                print(
                    'WARNING: ESC/POS PRINTING: ignoring invalid value: %s for style %s' % (style[attr], utfstr(attr)))
            else:
                _style[attr] = self.enforce_type(attr, style[attr])
        self.stack.append(_style)

    def set(self, style={}):
        """overrides style values at the current stack level"""
        _style = {}
        for attr in style:
            if attr in self.cmds and not style[attr] in self.cmds[attr]:
                print('WARNING: ESC/POS PRINTING: ignoring invalid value: %s for style %s' % (style[attr], attr))
            else:
                self.stack[-1][attr] = self.enforce_type(attr, style[attr])

    def pop(self):
        """ pop a style stack level """
        if len(self.stack) > 1:
            self.stack = self.stack[:-1]

    def to_escpos(self):
        """ converts the current style to an escpos command string """
        cmd = b''
        ordered_cmds = sorted(self.cmds.items(), key=lambda kv: (kv[0], kv[1]['_order']))
        for style in ordered_cmds:
            cmd += style[1][self.get(style[0])]
        return cmd


class XmlSerializer:
    """
    Converts the xml inline / block tree structure to a string,
    keeping track of newlines and spacings.
    The string is outputted asap to the provided escpos driver.
    """

    def __init__(self, escpos):
        self.escpos = escpos
        self.stack = ['block']
        self.dirty = False

    def start_inline(self, stylestack=None):
        """ starts an inline entity with an optional style definition """
        self.stack.append('inline')
        if self.dirty:
            self.escpos._raw(' ')
        if stylestack:
            self.style(stylestack)

    def start_block(self, stylestack=None):
        """ starts a block entity with an optional style definition """
        if self.dirty:
            self.escpos._raw('\n')
            self.dirty = False
        self.stack.append('block')
        if stylestack:
            self.style(stylestack)

    def end_entity(self):
        """ ends the entity definition. (but does not cancel the active style!) """
        if self.stack[-1] == 'block' and self.dirty:
            self.escpos._raw('\n')
            self.dirty = False
        if len(self.stack) > 1:
            self.stack = self.stack[:-1]

    def pre(self, text):
        """ puts a string of text in the entity keeping the whitespace intact """
        if text:
            self.escpos.text(text)
            self.dirty = True

    def text(self, text):
        """ puts text in the entity. Whitespace and newlines are stripped to single spaces. """
        if text:
            text = utfstr(text)
            text = text.strip()
            text = re.sub('\s+', ' ', text)
            if text:
                self.dirty = True
                self.escpos.text(text)

    def linebreak(self):
        """ inserts a linebreak in the entity """
        self.dirty = False
        self.escpos._raw('\n')

    def style(self, stylestack):
        """ apply a style to the entity (only applies to content added after the definition) """
        self.raw(stylestack.to_escpos())

    def raw(self, raw):
        """ puts raw text or escpos command in the entity without affecting the state of the serializer """
        self.escpos._raw(raw)


class XmlLineSerializer:
    """
    This is used to convert a xml tree into a single line, with a left and a right part.
    The content is not output to escpos directly, and is intended to be fedback to the
    XmlSerializer as the content of a block entity.
    """

    def __init__(self, indent=0, tabwidth=2, width=48, ratio=0.5):
        self.tabwidth = tabwidth
        self.indent = indent
        self.width = max(0, width - int(tabwidth * indent))
        self.lwidth = int(self.width * ratio)
        self.rwidth = max(0, self.width - self.lwidth)
        self.clwidth = 0
        self.crwidth = 0
        self.lbuffer = ''
        self.rbuffer = ''
        self.left = True

    def _txt(self, txt):
        if self.left:
            if self.clwidth < self.lwidth:
                txt = txt[:max(0, self.lwidth - self.clwidth)]
                self.lbuffer += txt
                self.clwidth += len(txt)
        else:
            if self.crwidth < self.rwidth:
                txt = txt[:max(0, self.rwidth - self.crwidth)]
                self.rbuffer += txt
                self.crwidth += len(txt)

    def start_inline(self, stylestack=None):
        if (self.left and self.clwidth) or (not self.left and self.crwidth):
            self._txt(' ')

    def start_block(self, stylestack=None):
        self.start_inline(stylestack)

    def end_entity(self):
        pass

    def pre(self, text):
        if text:
            self._txt(text)

    def text(self, text):
        if text:
            text = utfstr(text)
            text = text.strip()
            text = re.sub('\s+', ' ', text)
            if text:
                self._txt(text)

    def linebreak(self):
        pass

    def style(self, stylestack):
        pass

    def raw(self, raw):
        pass

    def start_right(self):
        self.left = False

    def get_line(self):
        return ' ' * self.indent * self.tabwidth + self.lbuffer + ' ' * (
                self.width - self.clwidth - self.crwidth) + self.rbuffer


class Escpos(EscposCore):
    """ ESC/POS Printer object """
    device = None
    encoding = None
    img_cache = {}

    def _check_image_size(self, size):
        """ Check and fix the size of the image to 32 bits """
        if size % 32 == 0:
            return (0, 0)
        else:
            image_border = 32 - (size % 32)
            if (image_border % 2) == 0:
                return (int(image_border / 2), int(image_border / 2))
            else:
                return (int(image_border / 2), int((image_border / 2) + 1))

    def _print_image(self, line, size):
        """ Print formatted image """
        i = 0
        cont = 0
        buffer = ""

        self._raw(S_RASTER_N)
        buffer = b"%02X%02X%02X%02X" % (int((size[0] / size[1]) / 8), 0, size[1], 0)
        self._raw(codecs.decode(buffer, 'hex'))
        buffer = ""

        while i < len(line):
            hex_string = int(line[i:i + 8], 2)
            buffer += "%02X" % hex_string
            i += 8
            cont += 1
            if cont % 4 == 0:
                self._raw(codecs.decode(buffer, "hex"))
                buffer = ""
                cont = 0

    def _raw_print_image(self, line, size, output=None):
        """ Print formatted image """
        i = 0
        cont = 0
        buffer = ""
        raw = b""

        def __raw(string):
            if output:
                output(string)
            else:
                self._raw(string)

        raw += S_RASTER_N
        buffer = "%02X%02X%02X%02X" % (int((size[0] / size[1]) / 8), 0, size[1], 0)
        raw += codecs.decode(buffer, 'hex')
        buffer = ""

        while i < len(line):
            hex_string = int(line[i:i + 8], 2)
            buffer += "%02X" % hex_string
            i += 8
            cont += 1
            if cont % 4 == 0:
                raw += codecs.decode(buffer, 'hex')
                buffer = ""
                cont = 0

        return raw

    def _convert_image(self, im):
        """ Parse image and prepare it to a printable format """
        pixels = []
        pix_line = ""
        im_left = ""
        im_right = ""
        switch = 0
        img_size = [0, 0]

        if im.size[0] > 512:
            print("WARNING: Image is wider than 512 and could be truncated at print time ")
        if im.size[1] > 255:
            raise ImageSizeError()

        im_border = self._check_image_size(im.size[0])
        for i in range(im_border[0]):
            im_left += "0"
        for i in range(im_border[1]):
            im_right += "0"

        for y in range(im.size[1]):
            img_size[1] += 1
            pix_line += im_left
            img_size[0] += im_border[0]
            for x in range(im.size[0]):
                img_size[0] += 1
                RGB = im.getpixel((x, y))
                im_color = (RGB[0] + RGB[1] + RGB[2])
                im_pattern = "1X0"
                pattern_len = len(im_pattern)
                switch = (switch - 1) * (-1)
                for x in range(pattern_len):
                    if im_color <= (255 * 3 / pattern_len * (x + 1)):
                        if im_pattern[x] == "X":
                            pix_line += "%d" % switch
                        else:
                            pix_line += im_pattern[x]
                        break
                    elif im_color > (255 * 3 / pattern_len * pattern_len) and im_color <= (255 * 3):
                        pix_line += im_pattern[-1]
                        break
            pix_line += im_right
            img_size[0] += im_border[1]

        return (pix_line, img_size)

    def print_base64_image(self, img):

        print('print_b64_img')

        id = hashlib.md5(img.encode()).digest()

        if id not in self.img_cache:
            print('not in cache')

            img = img[img.find(',') + 1:]
            f = io.BytesIO(b'img')
            f.write(base64.decodebytes(img.encode()))
            f.seek(0)
            img_rgba = Image.open(f)
            img = Image.new('RGB', img_rgba.size, (255, 255, 255))
            channels = img_rgba.split()
            if len(channels) > 3:
                # use alpha channel as mask
                img.paste(img_rgba, mask=channels[3])
            else:
                img.paste(img_rgba)

            print('convert image')

            pix_line, img_size = self._convert_image(img)

            print('print image')

            buffer = self._raw_print_image(pix_line, img_size)
            self.img_cache[id] = buffer

        print('raw image')

        self._raw(self.img_cache[id])

    def receipt(self, xml):
        """
        Prints an xml based receipt definition
        """

        def strclean(string):
            if not string:
                string = ''
            string = string.strip()
            string = re.sub('\s+', ' ', string)
            return string

        def format_value(value, decimals=3, width=0, decimals_separator='.', thousands_separator=',', autoint=False,
                         symbol='', position='after'):
            decimals = max(0, int(decimals))
            width = max(0, int(width))
            value = float(value)

            if autoint and math.floor(value) == value:
                decimals = 0
            if width == 0:
                width = ''

            if thousands_separator:
                formatstr = "{:" + str(width) + ",." + str(decimals) + "f}"
            else:
                formatstr = "{:" + str(width) + "." + str(decimals) + "f}"

            ret = formatstr.format(value)
            ret = ret.replace(',', 'COMMA')
            ret = ret.replace('.', 'DOT')
            ret = ret.replace('COMMA', thousands_separator)
            ret = ret.replace('DOT', decimals_separator)

            if symbol:
                if position == 'after':
                    ret = ret + symbol
                else:
                    ret = symbol + ret
            return ret

        def print_elem(stylestack, serializer, elem, indent=0):

            elem_styles = {
                'h1': {'bold': 'on', 'size': 'double'},
                'h2': {'size': 'double'},
                'h3': {'bold': 'on', 'size': 'double-height'},
                'h4': {'size': 'double-height'},
                'h5': {'bold': 'on'},
                'em': {'font': 'b'},
                'b': {'bold': 'on'},
            }

            stylestack.push()
            if elem.tag in elem_styles:
                stylestack.set(elem_styles[elem.tag])
            stylestack.set(elem.attrib)

            if elem.tag in (
                    'p', 'div', 'section', 'article', 'receipt', 'header', 'footer', 'li', 'h1', 'h2', 'h3', 'h4',
                    'h5'):
                serializer.start_block(stylestack)
                serializer.text(elem.text)
                for child in elem:
                    print_elem(stylestack, serializer, child)
                    serializer.start_inline(stylestack)
                    serializer.text(child.tail)
                    serializer.end_entity()
                serializer.end_entity()

            elif elem.tag in ('span', 'em', 'b', 'left', 'right'):
                serializer.start_inline(stylestack)
                serializer.text(elem.text)
                for child in elem:
                    print_elem(stylestack, serializer, child)
                    serializer.start_inline(stylestack)
                    serializer.text(child.tail)
                    serializer.end_entity()
                serializer.end_entity()

            elif elem.tag == 'value':
                serializer.start_inline(stylestack)
                serializer.pre(format_value(
                    elem.text,
                    decimals=stylestack.get('value-decimals'),
                    width=stylestack.get('value-width'),
                    decimals_separator=stylestack.get('value-decimals-separator'),
                    thousands_separator=stylestack.get('value-thousands-separator'),
                    autoint=(stylestack.get('value-autoint') == 'on'),
                    symbol=stylestack.get('value-symbol'),
                    position=stylestack.get('value-symbol-position')
                ))
                serializer.end_entity()

            elif elem.tag == 'line':
                width = stylestack.get('width')
                if stylestack.get('size') in ('double', 'double-width'):
                    width = width / 2

                lineserializer = XmlLineSerializer(stylestack.get('indent') + indent, stylestack.get('tabwidth'), width,
                                                   stylestack.get('line-ratio'))
                serializer.start_block(stylestack)
                for child in elem:
                    if child.tag == 'left':
                        print_elem(stylestack, lineserializer, child, indent=indent)
                    elif child.tag == 'right':
                        lineserializer.start_right()
                        print_elem(stylestack, lineserializer, child, indent=indent)
                serializer.pre(lineserializer.get_line())
                serializer.end_entity()

            elif elem.tag == 'ul':
                serializer.start_block(stylestack)
                bullet = stylestack.get('bullet')
                for child in elem:
                    if child.tag == 'li':
                        serializer.style(stylestack)
                        serializer.raw(' ' * indent * stylestack.get('tabwidth') + bullet)
                    print_elem(stylestack, serializer, child, indent=indent + 1)
                serializer.end_entity()

            elif elem.tag == 'ol':
                cwidth = len(str(len(elem))) + 2
                i = 1
                serializer.start_block(stylestack)
                for child in elem:
                    if child.tag == 'li':
                        serializer.style(stylestack)
                        serializer.raw(' ' * indent * stylestack.get('tabwidth') + ' ' + (str(i) + ')').ljust(cwidth))
                        i = i + 1
                    print_elem(stylestack, serializer, child, indent=indent + 1)
                serializer.end_entity()

            elif elem.tag == 'pre':
                serializer.start_block(stylestack)
                serializer.pre(elem.text)
                serializer.end_entity()

            elif elem.tag == 'hr':
                width = stylestack.get('width')
                if stylestack.get('size') in ('double', 'double-width'):
                    width = width / 2
                serializer.start_block(stylestack)
                serializer.text('-' * width)
                serializer.end_entity()

            elif elem.tag == 'br':
                serializer.linebreak()

            elif elem.tag == 'img':
                if 'src' in elem.attrib and 'data:' in elem.attrib['src']:
                    self.print_base64_image(elem.attrib['src'])

            elif elem.tag == 'barcode' and 'encoding' in elem.attrib:
                serializer.start_block(stylestack)
                self.barcode(strclean(elem.text), elem.attrib['encoding'])
                serializer.end_entity()

            elif elem.tag == 'cut':
                self.cut()
            elif elem.tag == 'partialcut':
                self.cut(mode='part')
            elif elem.tag == 'cashdraw':
                self.cashdraw(2)
                self.cashdraw(5)

            stylestack.pop()

        try:
            stylestack = StyleStack()
            serializer = XmlSerializer(self)
            root = ET.fromstring(xml.encode('utf-8'))

            self._raw(stylestack.to_escpos())

            print_elem(stylestack, serializer, root)

            if 'open-cashdrawer' in root.attrib and root.attrib['open-cashdrawer'] == 'true':
                self.cashdraw(2)
                self.cashdraw(5)
            if not 'cut' in root.attrib or root.attrib['cut'] == 'true':
                self.cut()

        except Exception as e:
            errmsg = str(e) + '\n' + '-' * 48 + '\n' + traceback.format_exc() + '-' * 48 + '\n'
            self.set(font='b')
            self.text(errmsg)
            self.cut()

            raise e
