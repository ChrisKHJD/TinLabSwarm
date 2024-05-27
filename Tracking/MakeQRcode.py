import qrcode

img = qrcode.make('robot_1')

print(type(img))
print(img.size)
# <class 'qrcode.image.pil.PilImage'>
# (290, 290)

img.save('qrcode/qrcode_test_1.png')