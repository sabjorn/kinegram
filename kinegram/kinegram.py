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

        self.interWidth = np.nan
        self.interHeight = np.nan
        self.interDepth = np.nan
        self.dtype = 'uint8'

        self.interlaceWidth = None
        self.overlay = None

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
        self.interlaceWidth = width * num_imgs
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

    def generateOverlay(self, overlap):
        """ Generates foreground image (interference image)
            overlap = [0, 1] width of opaque vs transpartent section
        """
        if self.interlaceWidth is None:
            raise Exception('you must generateInterlace before you can generate the Front')

        overlap_actual = int(self.interlaceWidth * overlap) # no of pixels
        overlay_modual = np.zeros((self.interHeight, self.interlaceWidth, 4), dtype=self.dtype)
        overlay_modual[:, 0:overlap_actual, 3] = 255 # opacity up

        # stack overlaps
        stack_amount = int(self.interlaced.shape[1] / self.interlaceWidth) - 1
        self.overlay = np.copy(overlay_modual)
        for i in np.arange(stack_amount):
            self.overlay = np.hstack((self.overlay, overlay_modual))

    def save(self, filename, directory="./"):
        """ exports interlaced and overlay as png images
        """
        Image.fromarray(self.interlaced).save("{0}{1}_interlaced.png".format(directory, filename))
        Image.fromarray(self.overlay).save("{0}{1}_overlayed.png".format(directory, filename))

if __name__ == '__main__':
    kine = Kinegram()
    for i in np.arange(0, 9, 3):
        kine.loadImage("./examples/dance/dance00{0}.png".format(i+1))

    kine.generateInterlace(width=2)
    kine.generateOverlay(.5)