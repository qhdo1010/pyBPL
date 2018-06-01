"""
Spatial model class definition.
"""

import numpy as np

from .spatial_hist import SpatialHist


class SpatialModel(object):
    """
    Stores a set of SpatialHist's, one for each stroke position, and can
    evaluate the likelihood/sample new positions.
    """

    def __init__(
            self, data_start, data_id, clump_id, xlim, ylim,
            nbin_per_side, prior_count
    ):
        """
        Initialize the SpatialModel class instance.

        :param data_start:
        :param data_id:
        :param clump_id:
        :param xlim: [1 x 2] range of x-dimension
        :param ylim: [1 x 2] range of y-dimension
        :param nbin_per_side: number of bins per dimension
        :param prior_count: prior counts in each cell (not added to edge cells)
        """

        assert np.prod(data_id.shape) == len(data_start)

        # Learn specific spatial models
        self.list_SH = []
        for i in range(clump_id-1):
            sh = SpatialHist(
                data_start[data_id==i], xlim, ylim, nbin_per_side, prior_count
            )
            self.list_SH.append(sh)

        # lump together datapoints from strokes after and including clump_id
        sh = SpatialHist(
            data_start[data_id>=clump_id], xlim, ylim, nbin_per_side,
            prior_count
        )
        self.list_SH.append(sh)

    def get_last_model_id(self):
        """
        Stroke ids after this are given to the same model (inclusive)

        :return:
            out: [scalar] id of the last model
        """
        return out

    def score(self, data_start, data_id):
        """
        Compute log-likelihood of new points

        :param data_start: [n x 2] positions
        :param data_id: [n x 1] the stroke index of each position
        :return:
            ll: [scalar] total log-likelihood
        """
        return ll

    def score_vec(self, data_start, data_id):
        """
        Compute log-likelihood of new points, and return breakdown for each one

        :param data_start: [n x 2] positions
        :param data_id: [n x 1] the stroke index of each position
        :return:
            ll: [n x 1] the log-likelihood of each position
        """
        return ll

    def sample(self, data_id):
        """
        Sample new stroke start positions

        :param data_id: [nsamp x 1] the stroke index of each position
        :return:
            samples: [nsamp x 2] positions drawn from the model
        """
        return samples

    def plot(self):
        """
        Plot the array of position models

        :return: None
        """
        return

    def __map_indx(self, old_id):
        """
        Map stroke ids to new ids

        :param old_id:
        :return:
            new_id:
        """
        return new_id