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
    """ A class for generating Kinegrams
            pxlWidth = width of each interlace "frame" in pixels
            rotation = angle to rotate image overlay (in degrees)
            backgroundDistance = distance from viewer to background image
            overlayDistance = distance from viewer to overlay (interference) image
    """
    def __init__(self, pxlWidth=1, rotation=0, backgroundDistance=1, overlayDistance=1):
        self.logger = logging.getLogger("kinegram")
        self.logger.debug("kinegram created")

        self.dpm = (300 / 0.0254) # const

        self.setPixelWidth(pxlWidth)

        self.rotation = rotation

        self.bg_im = []

        self.interWidth = np.nan
        self.interHeight = np.nan
        self.interDepth = np.nan
        self.dtype = 'uint8'

        self.setParallaxRatio(overlayDistance, backgroundDistance)

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

    def generateInterlace(self, orientation=0):
        """ Generates interlaced background image
            orientation = direction of interlace

            Note: crops input images to be even multiple of self.pxlWidth
            Note orientation currently does nothing
        """
        num_imgs = len(self.bg_im)
        stepsize = self.pxlWidth * num_imgs
        cropWidth = int(np.floor(self.interWidth / stepsize) * stepsize)
        self.interlaceWidth = self.pxlWidth * num_imgs

        self.interlaced = np.zeros(
            (self.interHeight, cropWidth, self.interDepth),
            dtype=self.bg_im[0].dtype
        )
        
        for i, img in enumerate(self.bg_im):
            img_crop = img[:,:cropWidth, :]
            for j in np.arange(self.pxlWidth):
                self.interlaced[:, ((i * self.pxlWidth)+j)::num_imgs*self.pxlWidth, :] = img_crop[:, j::stepsize, :]

    def generateOverlay(self, overlap):
        """ Generates foreground image (interference image)
            overlap = [0, 1] self.pxlWidth of opaque vs transpartent section
        """
        if self.interlaceWidth is None:
            raise Exception('you must generateInterlace before you can generate the Front')

        interlaceWidthAdjusted = int(self.interlaceWidth * self.parallaxRatio)
        if(interlaceWidthAdjusted < 1):
            raise Exception('interlace width is sub 1px. Either increase pxlWidth or change parallax ratio')
        overlap_actual = int(interlaceWidthAdjusted * overlap) # no of pixels
        overlay_modual = np.zeros((self.interHeight, interlaceWidthAdjusted, 4), dtype=self.dtype)
        overlay_modual[:, 0:overlap_actual, 3] = 255 # opacity up

        # stack overlaps
        stack_amount = int(self.interlaced.shape[1] / interlaceWidthAdjusted) - 1
        self.overlay = np.copy(overlay_modual)
        for i in np.arange(stack_amount):
            self.overlay = np.hstack((self.overlay, overlay_modual))

    def getAnimationPeriod(self):
        """ 
            Returns the animation period in meters
        """
        return (self.interlaceWidth / self.dpm)

    def setParallaxRatio(self, overlayDistance, backgroundDistance):
        """ 
            set the Parallax Ratio used to calculate the pixel width
            of the interlace image. This accounts for the effects of parallax

            overlayDistance = distance from viewer to interference overlay
            backgroundDistance = distance from viewer to the background animation

            NOTE: must regenerate overlay after setting this
        """
        self.parallaxRatio = overlayDistance / backgroundDistance

    def setPixelWidth(self, pxlWidth):
        """
            set the Pixel Width for animation frame
            pxlWidth = number of pixels wide for animation frame

            NOTE: after this is set, generateInterlace() must be run again
        """ 
        self.pxlWidth = max(pxlWidth, 1)

    def save(self, filename, directory="./"):
        """ exports interlaced and overlay as png images
        """
        Image.fromarray(self.interlaced).save("{0}{1}_interlaced.png".format(directory, filename))
        Image.fromarray(self.overlay).save("{0}{1}_overlayed.png".format(directory, filename))

if __name__ == '__main__':
    kine = Kinegram(pxlWidth=3)
    for i in np.arange(0, 9, 4):
        kine.loadImage("./examples/dance/dance00{0}.png".format(i+1))

    kine.generateInterlace()
    kine.generateOverlay(.5)

    ## calculate the viewer movement necessary for 1 animation cycle
    """
        X/D1 = P/D2
        X = viewer movement distance (m), i.e. how far viewer has to move to see animation
        P = Animation period (m)
        D1 = Distance from foreground to background
        D2 = Distance from viewer to foreground
    """
    backgroundDistance = 1
    overlayDistance = D1 = .9
    D2 = backgroundDistance - D1 
    """
        X = P * D1 / D2
    """
    viewerMovementDistance = kine.getAnimationPeriod() * D1 / D2
    
    ## NOTE generateOverlay needs a scaling parameter for generating the offsets for distance from background. Should be possible to do after as well

    # use equation `p/D1 = x/D2` to define the image sizes.