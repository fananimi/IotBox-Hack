import zpl
import qrcode

debug = False

width = 74
height = 52
dpmm = 8
zero_pint = [4, 2]
margin = 2

l = zpl.Label(height, width, dpmm=dpmm)

x = zero_pint[0]
y = zero_pint[1]
l.origin(x, y)
# BORDER FULL
l.draw_box((width * dpmm) - (2.5 * margin * dpmm), (height * dpmm) - (1.5 * margin * dpmm), thickness=3)
l.endorigin()

# TITLE
l.origin(x, y + 1.5)
l.write_text("INFORMASI SERVIS KENDARAAN", char_height=3, char_width=3, justification='C', line_width=width-5)
l.endorigin()

# HEADERR
l.origin(x, y + 5)
l.draw_box((width * dpmm) - (2.5 * margin * dpmm), 15 * dpmm, thickness=3)
l.endorigin()

# LEFT HEADERR
l.origin(x, y + 6.5)
l.write_text("OM JON", char_height=4, char_width=4, justification='C', line_width=16)
l.endorigin()

l.origin(x, y + 10.5)
l.write_text("Family General", char_height=2, char_width=2, justification='C', line_width=15)
l.endorigin()

l.origin(x, y + 12.5)
l.write_text("Service", char_height=2, char_width=2, justification='C', line_width=15)
l.endorigin()

l.origin(x, y + 15.5)
l.write_text("085853575796", char_height=2.5, char_width=2.5, justification='C', line_width=16)
l.endorigin()

l.origin(x + 15, y + 5)
l.draw_box(0, 15 * dpmm, thickness=3)
l.endorigin()

# # RIGHT HEADER
l.origin(x + 15, y + 10)
l.draw_box(54 * dpmm, 0, thickness=3)
l.endorigin()

l.origin(x + 17, y + 6.5)
l.write_text("Customer :", char_height=2.5, char_width=2.5, justification='L')
l.endorigin()

l.origin(x + 15, y + 11.5)
l.write_text("No Pol", char_height=2.5, char_width=2.5, justification='C', line_width=20)
l.endorigin()

l.origin(x + 35, y + 10)
l.draw_box(0, 10 * dpmm, thickness=3)
l.endorigin()

l.origin(x + 35, y + 11.5)
l.write_text("KM Mesin", char_height=2.5, char_width=2.5, justification='C', line_width=20)
l.endorigin()

l.origin(x + 55, y + 10)
l.draw_box(0, 10 * dpmm, thickness=3)
l.endorigin()

l.origin(x + 55, y + 11.5)
l.write_text("Tanggal", char_height=2.5, char_width=2.5, justification='C', line_width=15)
l.endorigin()

l.origin(x + 59.5, y + 15)
l.draw_box(0, 5 * dpmm, thickness=3)
l.endorigin()

l.origin(x + 64.5, y + 15)
l.draw_box(0, 5 * dpmm, thickness=3)
l.endorigin()

l.origin(x + 15, y + 15)
l.draw_box(54 * dpmm, 0, thickness=3)
l.endorigin()

# BODY 1
y += 20
l.origin(x + 35, y)
l.draw_box(0, 29 * dpmm, thickness=3)
l.endorigin()

l.origin(x, y + 1.5)
l.write_text("STATUS SERVIS", char_height=2.5, char_width=2.5, justification='C', line_width=35)
l.endorigin()

l.origin(x + 35, y + 0.5)
l.write_text("Ganti Oli Berikutnya", char_height=2, char_width=2, justification='C', line_width=35)
l.endorigin()

l.origin(x + 35, y + 2.5)
l.write_text("KM Mesin", char_height=2.5, char_width=2.5, justification='C', line_width=20)
l.endorigin()

l.origin(x + 48, y + 2.5)
l.write_text("/", char_height=2.5, char_width=2.5, justification='C', line_width=15)
l.endorigin()

l.origin(x + 55, y + 2.5)
l.write_text("Tanggal", char_height=2.5, char_width=2.5, justification='C', line_width=15)
l.endorigin()

l.origin(x + 55, y + 5)
l.draw_box(0, 5 * dpmm, thickness=3)
l.endorigin()

l.origin(x + 60, y + 5)
l.draw_box(0, 5 * dpmm, thickness=3)
l.endorigin()

l.origin(x + 65, y + 5)
l.draw_box(0, 5 * dpmm, thickness=3)
l.endorigin()

l.origin(x, y + 5)
l.draw_box((width * dpmm) - (2.5 * margin * dpmm), 0, thickness=3)
l.endorigin()

l.origin(x + 35, y + 9.8)
l.draw_box((34 * dpmm), 0, thickness=3)
l.endorigin()


# BODY 2
y += 5
l.origin(x + 1, y + 1.5)
l.write_text("Oli Mesin :", char_height=2, char_width=2, justification='L', line_width=35)
l.endorigin()

l.origin(x, y + 4.75)
l.draw_box((35 * dpmm), 0, thickness=3)
l.endorigin()

y += 4.75
l.origin(x + 1, y + 1.5)
l.write_text("Oli Perseneling :", char_height=2, char_width=2, justification='L', line_width=35)
l.endorigin()

l.origin(x, y + 4.75)
l.draw_box((35 * dpmm), 0, thickness=3)
l.endorigin()

y += 4.75
l.origin(x + 1, y + 1.5)
l.write_text("Oli Gardan :", char_height=2, char_width=2, justification='L', line_width=35)
l.endorigin()

l.origin(x, y + 4.75)
l.draw_box((35 * dpmm), 0, thickness=3)
l.endorigin()

y += 4.75
l.origin(x + 1, y + 1.5)
l.write_text("Filter Oli :", char_height=2, char_width=2, justification='L', line_width=35)
l.endorigin()

l.origin(x, y + 4.75)
l.draw_box((35 * dpmm), 0, thickness=3)
l.endorigin()

y += 4.75
l.origin(x + 1, y + 1.5)
l.write_text("Minyak Rem :", char_height=2, char_width=2, justification='L', line_width=35)
l.endorigin()

# QR CODE
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=1,
    border=4,
)
data = "WO-" + str(1).rjust(5, "0")
qr.add_data(data)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
image_width = 25
l.origin(x + 40, y - 17.25)
image_height = l.write_graphic(
    img,
    image_width)
l.endorigin()

l.origin(x + 40, y - 15)
l.write_text(data, char_height=2, char_width=2, justification='C', line_width=19, orientation='B', font='1')
l.endorigin()

# HELPER

if debug:
    x = 4
    y = 2
    for c in range(1, 16):
        l.origin(x, y)
        l.write_text(str(c), char_height=2, char_width=2, justification='C', line_width=5)
        l.endorigin()

        l.origin(x, y)
        l.draw_box(1, height * dpmm, thickness=0.5)
        l.endorigin()
        x += 5

    # LINE OF PRODUCT DESCRIPTION
    x = 4
    y = 2
    for r in range(1, 12):
        l.origin(x, y)
        l.write_text(str(r), char_height=2, char_width=2, justification='C', line_width=5)
        l.endorigin()

        l.origin(x, y)
        l.draw_box(width * dpmm, 1, thickness=0.5)
        l.endorigin()
        y += 5





# # QR CODE TEXT
# y += image_width - margin
# l.origin(margin, y)
# l.write_text(data['code'], char_height=2, char_width=2, justification='C', line_width=22)
# l.endorigin()
#
# # RIGHT LINE
# l.origin(image_height, margin * 2)
# l.draw_box(1, 322, thickness=3)
# l.endorigin()
#
# # UoM
# y = 10
# x = image_width + 2
# l.origin(x, y)
# l.write_text("UoM:", char_height=2, char_width=2, justification='L', line_width=20)
# l.endorigin()
#
# x += 5
# y -= 2
# l.origin(x, y)
# l.write_text(data['uom'], char_height=5, char_width=5, justification='L', line_width=20)
# l.endorigin()
#
# x = image_width
# y += 5
# l.origin(x, y)
# l.draw_box(260, 1, thickness=3)
# l.endorigin()
#
# # Qty
# y += 2
# x = image_width + 2
# l.origin(x, y)
# l.write_text("Qty:", char_height=2, char_width=2, justification='L', line_width=20)
# l.endorigin()
#
# x = image_width
# y += 3
# l.origin(x, y)
# l.draw_box(260, 1, thickness=3)
# l.endorigin()
#
# # LOCATIONS
# y += 2
# x = image_width + 2
# l.origin(x, y)
# l.write_text("Locations:", char_height=2, char_width=2, justification='L', line_width=20)
# l.endorigin()
#
# locations = data['locations']
# for location in locations:
#     y += 4
#     x = image_width + 2
#     l.origin(x, y)
#     l.write_text(location, char_height=3, char_width=3, justification='L', line_width=20)
#     l.endorigin()

# print(l.dumpZPL())
l.preview()
