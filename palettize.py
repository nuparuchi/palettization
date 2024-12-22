from PIL import Image
import sys
from pathlib import Path

#checks if a string is 6 characters and
#numbers 0-9 and letters A-F
def isRGB(code):
   if len(code) == 6:
        #47-58 are digits
        #65-70 are A-F
        for c in code.upper():
            n = ord(c)
            if not((n>=47 and n<=58) or (n>=65 and n<=70)):
                return False
        return True


#finds the sum of the differences of two colors
#which're here represented as tuples
def colorDiff(c1, c2):
   return abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2])


def main(image, args):
    #read args
    colors = []
    
    for arg in args:
        #see if it's a text document
        if arg[-4:] == ".txt":
            file = Path(arg)
            if file.is_file():
                #file exists, read colors from it
                with open(file, 'r') as file:
                    for line in file:
                        for word in line.split():
                            if isRGB(word):
                                colors.append(word.upper())

        #see if it's an rgb code
        else:
            if isRGB(arg):
                colors.append(arg.upper())

    #check that we have any colors at all
                
    #also, should keep track of dropped colors
    #and alert the user that we dropped them
    print(colors)
    if len(colors) == 0:
        print("No colors provided.")
        return False
    

    #palettize
    im = Image.open(image)

    out = Image.new('RGB', im.size)

    #oh and turn these hexcodes into rgb
    rgbColors = []
    for hex in colors:
       rgbColors.append(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4)))
       
    print(rgbColors)
    
    #iterate over pixels
    width, height = im.size

    #currently only looking at the exact pixels
    #should add a way to consider dithering too
    for x in range(width):
        for y in range(height):
            r,g,b = im.getpixel((x,y))

            closest = 0
            closeAmount = colorDiff((r,g,b), rgbColors[0])
            
            for i in range(1, len(rgbColors)):
               thisDiff = colorDiff((r,g,b), rgbColors[i])
               if thisDiff < closeAmount:
                  closeAmount = thisDiff
                  closest = i
               
            
            out.putpixel((x,y), rgbColors[closest])

    newName = image[:-4] + "-palettize" + image[-4:]
    out.save(newName)

#feed main the image path & the args
main(sys.argv[1], sys.argv[2:])









