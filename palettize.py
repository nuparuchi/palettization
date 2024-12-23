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


#find average of two colors
#weight is the value of the first color out of 1
#default is 0.5 for an even mix
#probably shouldnt use weights >1 or <0
def avgColor(c1, c2, weight=0.5):
    weight2 = 1 - weight
    newR = c1[0]*weight + c2[0]*weight2
    newG = c1[1]*weight + c2[1]*weight2
    newB = c1[2]*weight + c2[2]*weight2
    return (newR, newG, newB)


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
       
    #print(rgbColors)
    #populate two & four dithered color lists
    #2 dithered means 1 then 1 repeat
    #4 dithered means 1 then 3 repeat
    dithered = []
       
    threshold = 0.5
    threshVal = threshold * (255*3) #only include pairs that are
    #similar enough (ie not a big difference between them determined)
    #as well as different enough (big enough difference between them)
    #by the threshold value
    for i in range(len(rgbColors)):
       for j in range(len(rgbColors)-i):
          #j+i because we want the last ones
          ditherDiff = colorDiff(rgbColors[i], rgbColors[j+i])
          if ditherDiff < threshVal:
              dithered.append((rgbColors[i], rgbColors[j+i]))
    
    #iterate over pixels
    width, height = im.size

    #currently only looking at the exact pixels
    #should add a way to consider dithering too
    for x in range(width):
        for y in range(height):
            r,g,b = im.getpixel((x,y))

            closest = 0
            closeAmount = colorDiff((r,g,b), rgbColors[0])

            #0: no dither
            #1: two-dither
            #2: four-dither favoring first
            #3: four-dither favoring latter
            ditherVal = 0
            
            for i in range(1, len(rgbColors)):
                thisDiff = colorDiff((r,g,b), rgbColors[i])
                if thisDiff < closeAmount:
                    closeAmount = thisDiff
                    closest = i
                    ditherVal = 0

            #do the same check but for dithered options
            weights = [0.5, 0.75, 0.25]
            
            for d in range(len(dithered)):
                #do once for equal, once for either
                #four-dithering
                for weight in weights:
                    mix = avgColor(dithered[d][0], dithered[d][1], weight)
                    thisDiff = colorDiff((r,g,b), mix)
                    if thisDiff < closeAmount:
                        closeAmount = thisDiff
                        closest = d + len(rgbColors)
                        if weight == 0.5:
                            ditherVal = 1
                        elif weight == 0.72:
                            ditherVal = 2
                        else:
                            ditherVal = 3

            if closest < len(rgbColors):
                chosen = rgbColors[closest]

            else:
                #we're in dither territory
                #we're looking at dithere[closest - len(rgbColors)]
                #and then either the [0] or [1] of that
                if ditherVal < 3: #favoring first color or equal
                    mainCol = dithered[closest - len(rgbColors)][0]
                    secondCol = dithered[closest - len(rgbColors)][1]
                else:
                    mainCol = dithered[closest - len(rgbColors)][1]
                    secondCol = dithered[closest - len(rgbColors)][0]

                #choose main unless we hit the 1/2 for two-dithering
                #or 1/4 for four-dithering
                ditherAmount = min(ditherVal,2)*2
                #gives 2 if two-dithering, 4 if four-dithering
                if (x + (y*(ditherAmount/2)))% ditherAmount == 0:
                    #we hit the secondary color
                    chosen = secondCol
                else: #we hit the main color
                    chosen = mainCol
                    
            
            out.putpixel((x,y), chosen)

    newName = image[:-4] + "-palettize" + image[-4:]
    out.save(newName)

#feed main the image path & the args
main(sys.argv[1], sys.argv[2:])









