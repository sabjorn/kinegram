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

def round(val):
    rem = val - int(val)
    if(rem >= .5): val = int(val) + 1
    return int(val)

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

        interlaceWidthScaled = round(self.interlaceWidth * self.parallaxRatio)
        self.logger.debug("Interlace Width (scaled): {0}".format(interlaceWidthScaled))
        if(interlaceWidthScaled < 1):
            raise Exception('interlace width is sub 1px. Either increase pxlWidth or change parallax ratio')
        overlap_actual = round(interlaceWidthScaled * overlap) # no of pixels
        self.logger.debug("Overlap Widths (scaled): {0} | {1}".format(overlap_actual, interlaceWidthScaled - overlap_actual))
        overlay_modual = np.zeros((self.interHeight, interlaceWidthScaled, 4), dtype=self.dtype)
        overlay_modual[:, 0:overlap_actual, 3] = 255 # opacity up

        # stack overlaps
        stack_amount = int(self.interlaced.shape[1] / interlaceWidthScaled) - 1
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
    logger = logging.getLogger()
    logging.basicConfig(format='%(message)s')
    logger.setLevel(logging.DEBUG)

    pxlWidth = 3
    # imageNumbers = np.array((10,  3,  2, 25, 23, 22, 15)) # head3
    # imageNumbers = np.array((21, 25, 29, 1, 5, 9, 13, 17)) # head4
    # imageNumbers = np.arange(1, 13) # head8
    # imageNumbers = np.arange(1, 32) # head4
    imageNumbers = np.array((1, 4, 7, 10, 14, 21, 25)) # head9

    overlapWidth = (len(imageNumbers) - 1)/len(imageNumbers)
    headname = "head9"
    imgdir = "./examples/heads/{0}/8.5x11/".format(headname)
    kine = Kinegram(pxlWidth=pxlWidth)
    for i in imageNumbers:
        kine.loadImage("./{0}/{1}_{2}.png".format(imgdir, headname, i))

    kine.generateInterlace()
    # kine.generateOverlay(overlapWidth)

    ## calculate the viewer movement necessary for 1 animation cycle
    """
        P/D1 = X/D2
        X = viewer movement distance (m), i.e. how far viewer has to move to see animation
        P = Animation period (m)
        D1 = Distance from foreground to background
        D2 = Distance from viewer to foreground
    """
    backgroundDistance = 1.0
    overlayDistance = D2 = .9 # .75 and .9 work well. >.5 seems to not work at all
    D1 = backgroundDistance - D2
    """
        X = P * D2 / D1
    """
    if(D1 > 0):
        viewerMovementDistance = kine.getAnimationPeriod() * D2 / D1
    else:
        viewerMovementDistance = kine.getAnimationPeriod()

    print("animation period:", kine.getAnimationPeriod())
    print("viewer animation period:",viewerMovementDistance)

    kine.setParallaxRatio(overlayDistance, backgroundDistance)
    kine.generateOverlay(overlapWidth)

    kine.save("{0}_8x11_{1}_{2}_{3}_{4}".format(headname, pxlWidth, len(kine.bg_im), overlapWidth, D1), directory=imgdir)
    
    ## NOTE generateOverlay needs a scaling parameter for generating the offsets for distance from background. Should be possible to do after as well

    # use equation `p/D1 = x/D2` to define the image sizes.