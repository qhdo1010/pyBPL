import unittest
import torch

from ..library import Library
from ..objects.part import vanilla_to_motor



class TestVanillaToMotor(unittest.TestCase):

    def setUp(self):
        self.lib = Library()

    def testV2M(self):
        ncpt = 5
        nsub = 3
        # shapes_token has shape (ncpt, 2, nsub)
        shapes_token = \
            [[[-57.40,  24.25,  39.48],
              [-24.32,  16.24, -19.35]],

             [[  2.67,   4.46, -36.31],
              [ 29.17, -22.95,  -2.88]],

             [[ 52.54, -22.68,  40.90],
              [-21.49,  53.78,  26.89]],

             [[-17.66,  18.58,  50.14],
              [ -2.22,   1.17, -16.29]],

             [[  7.58, -30.76, -34.80],
              [ 25.86, -61.31, -81.7337]]]
        shapes_token = torch.tensor(shapes_token)
        assert shapes_token.shape == torch.Size([ncpt, 2, nsub])
        # invscales_token has shape (nsub,)
        invscales_token = [0.51,  0.18,  0.14]
        invscales_token = torch.tensor(invscales_token)
        assert invscales_token.shape == torch.Size([nsub])
        # position has shape (2,)
        position = [ 74.25, -13.28]
        position = torch.tensor(position)
        assert position.shape == torch.Size([2])
        # call vanilla_to_motor
        motor, motor_spline = vanilla_to_motor(
            shapes_token, invscales_token, position
        )
        self.assertEqual(motor.shape, torch.Size([nsub,200,2]))
        self.assertEqual(motor_spline.shape, torch.Size([ncpt,2,nsub]))

if __name__ == '__main__':
    unittest.main()