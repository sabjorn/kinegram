import logging
import inspect

import numpy as np
from PIL import Image

def autolog(logger, message):
    """
        Automatically log the current function details.
    """
    # Get the previous frame in the stack
    func = inspect.currentframe().f_back.f_code
    # Dump the message + the name of this function to the log.
    logger.debug("%s: %s in %s:%i" % (
        message, 
        func.co_name, 
        func.co_filename, 
        func.co_firstlineno
    ))

class Kinegram(object):
    """A class for generating Kinegrams"""
    def __init__(self, rotation=0):
        self.logger = logging.getLogger("kinegram")
        self.logger.debug("kinegram created")

        self.rotation = rotation

        self.bg_im = []

        cropHeight = np.nan # guaranteed not minimum
        self.interWidth = np.nan
        self.interHeight = np.nan
        self.interDepth = np.nan
        self.dtype = 'uint8'

    def loadImage(self, filename):
        """ Loads image as PIL.Image type
            Appending to the background image list
        """
        self.appendImage(np.asarray(Image.open(filename).rotate(self.rotation)))

    def appendImage(self, img):
        """ Appends numpy array to bg_img list
        """
        # get minimum dimension
        self.interHeight = int(np.nanmin((img.shape[0], self.interHeight)))
        self.interWidth = int(np.nanmin((img.shape[1], self.interWidth)))
        self.interDepth = int(np.nanmin((img.shape[2], self.interDepth)))
        self.dtype = img.dtype
        self.bg_im.append(img)

    def generateInterlace(self, width=1, orientation=0):
        """ Generates interlaced background image
            width = width of each interlace "frame" in pixels
            orientation = direction of interlace

            Note: crops input images to be even multiple of width
            Note orientation currently does nothing
        """

        num_imgs = len(self.bg_im)
        cropWidth = int(np.floor(self.interWidth / width) * width)
        cropHeight = int(np.floor(self.interHeight / width) * width)

        self.interlaced = np.zeros(
            (self.interHeight, cropWidth * num_imgs, self.interDepth),
            dtype=self.bg_im[0].dtype
        )
        
        for i, img in enumerate(self.bg_im):
            img_crop = img[:,:cropWidth, :]
            for j in np.arange(width):
                self.interlaced[:, ((i * width)+j)::num_imgs*width, :] = img_crop[:, j::width, :]

if __name__ == '__main__':
    kine = Kinegram()
    # for i in np.arange(3):
    #     kine.loadImage("./examples/dance/dance00{0}.png".format(i+1))

    red = np.zeros((100, 100, 3), dtype='uint8')
    green = np.copy(red)
    blue = np.copy(red)

    red[:,:, 0] = 255
    green[:,:, 1] = 255
    blue[:,:, 2] = 255

    kine.appendImage(red)
    kine.appendImage(green)
    kine.appendImage(blue)

    kine.generateInterlace(width = 2)