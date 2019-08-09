"""
Automates scaling of input image to specific canvas size
"""
import os
import numpy as np
from PIL import Image


# user config
headnum = 8
startingDir = "./examples/heads/"
dpi = 300
width = 11
height = 8.5
imgRange = np.arange(1, 13)
###

for i in imgRange:
    head = "head{0}".format(headnum)
    imagedir = "{0}/{1}".format(startingDir, head)
    imagename = "{0}_{1}".format(head, i)

    # make white canvas
    canvasDim = (int(dpi*height), int(dpi*width), 4)
    canvasDimMin = min(canvasDim[:2])
    canvas = np.zeros(canvasDim, dtype='uint8')
    canvas[:,:,:] = 255

    # open image and scale to fit canvs
    im = Image.open("{0}/{1}.png".format(imagedir, imagename))
    imMaxDim = max(im.width, im.height)
    scale = canvasDimMin/imMaxDim
    scaleDim = (int(im.width*scale), int(im.height*scale))
    im = im.resize(scaleDim)

    # find centre of canvas and add scaled input image
    centre = (int(abs(canvas.shape[0] - im.height)/2),  int(abs(canvas.shape[1] - im.width)/2))
    canvas[centre[0]:im.height + centre[0], centre[1]:im.width + centre[1], :] += np.asarray(im)
    imout = Image.fromarray(canvas)


    # create output dir and save
    outdir = "{0}/{1}x{2}".format(imagedir, height, width)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    imout.save("{0}/{1}.png".format(outdir, imagename))
