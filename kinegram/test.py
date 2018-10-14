import unittest
from kinegram import Kinegram
import numpy as np

class SimpleKinegramTestCase(unittest.TestCase):
    def setUp(self):
        self.kine = Kinegram()

class TestKinegramMethods(SimpleKinegramTestCase):
    
    def test_appendImage_sequenceOrder(self):
        zero = np.zeros((10, 10, 3), dtype='uint8')
        one = np.copy(zero) + 1
        two = np.copy(zero) + 2

        self.kine.appendImage(zero)
        self.kine.appendImage(one)
        self.kine.appendImage(two)

        np.testing.assert_array_equal(self.kine.bg_im[0], zero)
        np.testing.assert_array_equal(self.kine.bg_im[1], one)
        np.testing.assert_array_equal(self.kine.bg_im[2], two)

    def test_appendImage_count(self):
        zero = np.zeros((10, 10, 3), dtype='uint8')

        for i in np.arange(10):
            self.kine.appendImage(zero)
            self.assertEqual(len(self.kine.bg_im), i+1)

    def test_generateInterlace_outputSize(self):
        num_img = 5
        height = 10
        width = 10
        layers = 3
        tmp = np.zeros((height, width, layers), dtype='uint8')

        for i in np.arange(num_img):
            self.kine.appendImage(tmp)
        
        self.kine.generateInterlace()
        np.testing.assert_array_equal(self.kine.interlaced.shape, tmp.shape)

    def test_generateInterlace_outputCroppedSize(self):
        '''
        The input images are cropped to be the closest
        whole division of width/num_img
        '''
        num_img = 4
        width = 10
        cropsize = 8 # new image width, the result of width/num_img 
        tmp = np.zeros((10, width, 3), dtype='uint8')

        for i in np.arange(num_img):
            self.kine.appendImage(tmp)
        
        self.kine.generateInterlace()
        self.assertEqual(self.kine.interlaced.shape[1], cropsize)

    def test_generateInterlace_checkPixelOrdering(self):
        pxl_width = 2
        base = np.zeros((1, pxl_width, 3), dtype='uint8')
        
        r = np.copy(base)
        r[:,:,0] = 255
        g = np.copy(base)
        g[:,:,1] = 255
        b = np.copy(base)
        b[:,:,2] = 255

        rgb = np.hstack((r,g,b))

        self.kine.appendImage(rgb)
        self.kine.appendImage(rgb)
        self.kine.appendImage(rgb)
        
        self.kine.generateInterlace(pxl_width=pxl_width)
        np.testing.assert_array_equal(self.kine.interlaced, np.hstack((r,r,r)))

    def test_generateOverlay_shape(self):
        num_img = 10
        base = np.zeros((1, 1, 4), dtype='uint8')
        
        for i in np.arange(num_img):
            self.kine.appendImage(base)

        self.kine.generateInterlace()
        self.kine.generateOverlay(.5)
        shape_test = np.copy(base.shape)
        shape_test[1] *= num_img
        np.testing.assert_array_equal(self.kine.overlay.shape, shape_test)

    def test_generateOverlay_overlapPixelCount(self):
        overlaps = np.linspace(0, 1., 10)
        for overlap in overlaps:
            self.kine = Kinegram() # need fresh one for all the tests
            num_img = 4
            width = 100
            height = 1
            pxl_width = 2

            base = np.zeros((height, width, 4), dtype='uint8')
            
            for i in np.arange(num_img):
                self.kine.appendImage(base)

            self.kine.generateInterlace(pxl_width=pxl_width)
            self.kine.generateOverlay(overlap)
            
            interlace_width = pxl_width * num_img
            overlay_section = self.kine.overlay[:, :interlace_width, :]
            opaque_width = int(overlay_section.shape[1] * overlap)
            np.testing.assert_array_equal(overlay_section[:, :opaque_width, 3], 255)
            np.testing.assert_array_equal(overlay_section[:, opaque_width:, 3], 0)

    def test_loadImage(self):
        # don't know how to test this
        None

if __name__ == '__main__':
    unittest.main()