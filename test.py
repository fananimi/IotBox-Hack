data = {
    'name': 'Test Name',
    'code': '0123456789',
    'uom': 'Unit(S)',
    'locations': [
        'SBY/Stock',
        'KSY/Stock'
    ]
}

import qrcode
import zpl

l = zpl.Label(72, 50)
margin = 3
x = y = margin

# BORDER
l.origin(x, y)
l.draw_box(525, 360, thickness=3)
l.endorigin()

# PRODUCT DESCRIPTION
y += 1
l.origin(margin, y)
l.write_text(data['name'], char_height=2, char_width=2, justification='C', line_width=42)
l.endorigin()

# LINE OF PRODUCT DESCRIPTION
y += 2
l.origin(x, y)
l.draw_box(525, 1, thickness=3)
l.endorigin()

# QR CODE
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=1,
    border=4,
)
qr.add_data(data['code'])
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
image_width = 25
y = int((l.height - image_width)/4) - 4
l.origin(1.75, y)
image_height = l.write_graphic(
    img,
    image_width)
l.endorigin()

# QR CODE TEXT
y += image_width - margin
l.origin(margin, y)
l.write_text(data['code'], char_height=2, char_width=2, justification='C', line_width=22)
l.endorigin()

# RIGHT LINE
l.origin(image_height, margin * 2)
l.draw_box(1, 322, thickness=3)
l.endorigin()

# UoM
y = 10
x = image_width + 2
l.origin(x, y)
l.write_text("UoM:", char_height=2, char_width=2, justification='L', line_width=20)
l.endorigin()

x += 5
y -= 2
l.origin(x, y)
l.write_text(data['uom'], char_height=5, char_width=5, justification='L', line_width=20)
l.endorigin()

x = image_width
y += 5
l.origin(x, y)
l.draw_box(260, 1, thickness=3)
l.endorigin()

# LOCATIONS
y += 2
x = image_width + 2
l.origin(x, y)
l.write_text("Locations:", char_height=2, char_width=2, justification='L', line_width=20)
l.endorigin()

locations = data['locations']
for location in locations:
    y += 4
    x = image_width + 2
    l.origin(x, y)
    l.write_text(location, char_height=3, char_width=3, justification='L', line_width=20)
    l.endorigin()

# print(l.dumpZPL())
l.preview()
