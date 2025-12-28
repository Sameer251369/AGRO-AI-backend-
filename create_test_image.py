from PIL import Image, ImageDraw
img = Image.new('RGB',(400,400),(34,139,34))
d = ImageDraw.Draw(img)
for i in range(5):
    x = 50 + i*60
    d.ellipse((x,100,x+40,140), fill=(139,69,19))
img.save('test_leaf.jpg')
print('saved test_leaf.jpg')
