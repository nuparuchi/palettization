from PIL import Image
import sys
from pathlib import Path
import pickle
import math

#checks if a string is 6 characters and
#numbers 0-9 and letters A-F
def isRGB(code):
    if len(code) == 6 or len(code) == 7:
        thisCode = code
        if len(code) == 7:
            if code[0] == '#':
                thisCode = code[1:]
        #47-58 are digits
        #65-70 are A-F
        for c in thisCode.upper():
            n = ord(c)
            if not((n>=47 and n<=58) or (n>=65 and n<=70)):
                return False
        return True
    return False

#use whichever color difference algorithm we're using
def colorDiff(c1, c2, diffType):
   match diffType:
       case 0:
           return taxicabDiff(c1, c2)
       case 1:
           return euclidDiff(c1, c2)

#finds the sum of the differences of two colors
#which're here represented as tuples
def taxicabDiff(c1, c2):
    return abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2])

#finds the euclidian distance of two colors
#which're here represented as tuples
def euclidDiff(c1, c2):
    return math.sqrt(((c1[0] - c2[0])**2) + ((c1[1] - c2[1])**2) + ((c1[2] - c2[2])**2))

#get average value of colors
#weight is relative amount of first color
#out of 1
#probably don't do weights outside of 0-1
def colorAvg(c1, c2, weight=0.5):
    weight2 = 1-weight
    newR = c1[0]*weight + c2[0]*weight2
    newG = c1[1]*weight + c2[1]*weight2
    newB = c1[2]*weight + c2[2]*weight2
    return (newR, newG, newB)

#load the colors and dict of color mappings
#from a given file
def loadPalette(file):
    with open(file, 'rb') as f:
        held = pickle.load(f)
    colors = held.pop(0)
    settings = held.pop(1, [])
    
    return colors, settings, held

def main(image, args):
    #read args
    colors = []
    settings = [1,1,0] #each setting gets a value here
                       #the first setting is dithering
                       #1 means the images are by default dithered
    
                       #the second setting is how much the image is compressed
                       #1 means no compression, any higher integer means
                       #that many pixels in a square are combined together
                       #so 2 would mean the image takes 2x2 squares of pixels
                       #instead of individual pixels

                       #the third setting is how we're calculating color difference
                       #0 is taxicab difference (default since it's fast)
                       #1 is euclid difference

    #make a dict to remember what color/dithering gets mapped
    #to each color of pixel
    held = {}

    #store name of palette if it does not currently exist
    palName = ""

    for arg in args:
        #see if it's a palette
        if arg[-4:] == ".pal":
            #store the palName
            #so we can update/create the palette when we're done
            palName = arg
            file = Path(arg)
            if file.is_file():
                #file exists, load palette
                #we need the colors, the dict, and the settings from the palette
                colors, tempSettings, held = loadPalette(file)
                for i in range(len(tempSettings)):
                    settings[i] = tempSettings[i]
                    #go through tempSettings and set settings from that
                    #this makes it so when we add settings in the future,
                    #old palettes will just use the default values of those
                    #settings, rather than not have them set at all
        
        #see if it's a text document
        if arg[-4:] == ".txt":
            if palName == '' or not Path(palName).is_file():
            #only read colors if we don't already have a palette
                file = Path(arg)
                if file.is_file():
                    #file exists, read colors from it
                    with open(file, 'r') as file:
                        for line in file:
                            for word in line.split():
                                if isRGB(word) and not word.upper() in colors:
                                    colors.append(word.upper())

        #see if it's a setting
        if arg[0] == '-':
            if palName == '' or not Path(palName).is_file():
            #only read settings if we don't already have a palette
                match arg:
                    case "-nodither":
                        settings[0] = 0
                    case "-euclid":
                        settings[2] = 1
                if arg[1:].isnumeric():
                    settings[1] = int(arg[1:])
        
        #see if it's an rgb code
        else:
            if palName == '' or not Path(palName).is_file():
                #only read color if we don't already have a palette
                if isRGB(arg) and not arg.upper() in colors:
                    colors.append(arg.upper())

    #check that we have any colors at all
                
    #also, should keep track of dropped colors
    #and alert the user that we dropped them
    print(colors)
    if len(colors) == 0:
        print("No colors provided.")
        return False

    #tell user about settings
    if settings[0]:
        print("Dithering on")
    else:
        print("Dithering off")

    if not settings[1] == 1:
        print("Shrinking each dimension by a factor of " + str(settings[1]))

    if settings[2] == 0:
        print("Using taxicab distance")
    elif settings[2] == 1:
        print("Using euclidean distance")
    

    #palettize
    im = Image.open(image)

    origWidth, origHeight = im.size
    width = origWidth//settings[1]
    height = origHeight//settings[1]

    out = Image.new('RGB', (width, height))

    #oh and turn these hexcodes into rgb
    rgbColors = []
    for hex in colors:
        rgbColors.append(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4)))
       
    #we've got colors, now introduce dithering options
    #we're going to populate a list of dithered color pairs
    #as well as calculate what those'll be in terms of averages
    #for 2-dithered and either way for 4-dithered
    dithered = []
    ditheredAvg = []

    weights = [0.5, 0.75, 0.25]

    #introduce a threshold
    #so we only dither with colors far enough apart but not too far apart
    upperThreshold = 0.3
    lowerThreshold = 0.15

    upThresholdVal  = upperThreshold * (255*3)
    lowThresholdVal = lowerThreshold * (255*3)

    #for each color
    if settings[0]:
        for i in range(len(rgbColors)):
            #and all successive colors
            #(ie all pairs without respect to order and no repeats)
            for j in range(len(rgbColors)-i-1):
                #check that this pair is within the thresholds
                ditherDiff = colorDiff(rgbColors[i], rgbColors[i+j+1], settings[2])
                #if it is...
                if ditherDiff < upThresholdVal and ditherDiff > lowThresholdVal:
                    #...put it in the list of potential ditherings
                    #and also include the average colors of those ditherings
                    dithered.append((rgbColors[i], rgbColors[i+j+1]))
                    ditheredAvg.append(tuple(colorAvg(rgbColors[i], rgbColors[i+j+1], weight) for weight in weights))

    
    #iterate over pixels

    #0 -> no dithering
    #1 -> two-dithered
    #2 -> four-dithered, first color
    #3 -> four-dithered, second color
    ditherVal = 0

    for x in range(width):
        for y in range(height):
            r,g,b = (0,0,0)
            for i in range(settings[1]):
                for j in range(settings[1]):
                    tempR,tempG,tempB = im.getpixel(((x*settings[1])+i,(y*settings[1])+j))
                    r += tempR
                    g += tempG
                    b += tempB

            r = r // settings[1]
            g = g // settings[1]
            b = b // settings[1]

            #get rgb as key for our dict of calculated values
            newKey = (r,g,b)

            #if we have not yet calculated the closest color,
            #calculate it
            if not newKey in held.keys():
                closest = 0
                closeAmount = colorDiff((r,g,b), rgbColors[0], settings[2])
            
                for i in range(1, len(rgbColors)):
                    thisDiff = colorDiff((r,g,b), rgbColors[i], settings[2])
                    if thisDiff < closeAmount:
                        closeAmount = thisDiff
                        closest = i
                        ditherVal = 0

                #now do the same for dithered options
                for i in range(len(dithered)):
                    for w in range(len(weights)):
                        thisDiff = colorDiff((r,g,b), ditheredAvg[i][w], settings[2])
                        if thisDiff < closeAmount:
                            closeAmount = thisDiff
                            closest = i
                            ditherVal = w + 1
                                
                #and save what we calculated in our dict
                held.update({newKey : (closest, ditherVal)})

            #otherwise simply get the value from the dict
            else:
                closest,ditherVal = held[newKey]
                

            if ditherVal == 0:
                out.putpixel((x,y), rgbColors[closest])

            else:
                #gives 2 for two-dithering,
                #and 4 for four-dithering
                ditherAmount = min(ditherVal, 2)*2

                if ditherVal < 3:
                    mainCol = dithered[closest][0]
                    secCol  = dithered[closest][1]
                else:
                    mainCol = dithered[closest][1]
                    secCol  = dithered[closest][0]

                if (x+(y*ditherAmount/2))%ditherAmount == 0:
                    out.putpixel((x,y), secCol)
                else:
                    out.putpixel((x,y), mainCol)
                

    #add "-palettize" to the name before .png or .jpg
    #should probably break at the final '.' and use that
    newName = image[:-4] + "-palettize" + image[-4:]
    out.save(newName)

    if (palName != ""): #some palName exists
        #save the palette under that name
        held.update({0 : colors})
        held.update({1 : settings})
        with open(palName, 'wb') as f:
            pickle.dump(held, f)

    return True


#feed main the image path & the args
main(sys.argv[1], sys.argv[2:])
