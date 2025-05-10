# palettization
Replace colors of an image with new colors. Probably actually posterization.

Current version takes input from console for the image to palettize, followed by any number of arguments, which are either a hexcode, a text file which is then read for hexcodes, or a palette file (.pal) which is either used in order to have to calculate fewer distances (if the .pal file exists) or saved to in order to be loaded in the future (if the .pal file does not exist). Then replaces all pixels in image with color from provided palette which is closest (by just taking the sum of differences of each component of the rgb values. May include other distance measures in the future).
