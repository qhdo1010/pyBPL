"""
Parts for sampling part tokens. Parts, together with relations between parts,
make up concepts.
"""
from abc import ABCMeta, abstractmethod
import torch

from .. import splines


class PartType(object):
    """
    An abstract base class for parts. Holds all type-level parameters of the
    part.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def parameters(self):
        """
        return list of parameters
        """
        pass

    @abstractmethod
    def lbs(self, eps=1e-4):
        """
        return list of lower bounds for parameters
        """
        pass

    @abstractmethod
    def ubs(self, eps=1e-4):
        """
        return list of upper bounds for parameters
        """
        pass

    def train(self):
        """
        makes params require grad
        """
        for param in self.parameters():
            param.requires_grad_(True)

    def eval(self):
        """
        makes params require no grad
        """
        for param in self.parameters():
            param.requires_grad_(False)

    def to(self, device):
        """
        moves parameters to device
        TODO
        """
        pass


class StrokeType(PartType):
    """
    Holds all type-level parameters of the stroke.

    Parameters
    ----------
    nsub : tensor
        scalar; number of sub-strokes
    ids : (nsub,) tensor
        sub-stroke ID sequence
    shapes : (ncpt, 2, nsub) tensor
        shapes types
    invscales : (nsub,) tensor
        invscales types
    """
    def __init__(self, nsub, ids, shapes, invscales):
        super(StrokeType, self).__init__()
        self.nsub = nsub
        self.ids = ids
        self.shapes = shapes
        self.invscales = invscales

    def parameters(self):
        """
        Returns a list of parameters that can be optimized via gradient descent.

        Returns
        -------
        parameters : list
            optimizable parameters
        """
        parameters = [self.shapes, self.invscales]

        return parameters

    def lbs(self, eps=1e-4):
        """
        Returns a list of lower bounds for each of the optimizable parameters.

        Parameters
        ----------
        eps : float
            tolerance for constrained optimization

        Returns
        -------
        lbs : list
            lower bound for each parameter
        """
        lbs = [None, torch.full(self.invscales.shape, eps)]

        return lbs

    def ubs(self, eps=1e-4):
        """
        Returns a list of upper bounds for each of the optimizable parameters.

        Parameters
        ----------
        eps : float
            tolerance for constrained optimization

        Returns
        -------
        ubs : list
            upper bound for each parameter
        """
        ubs = [None, None]

        return ubs


class PartToken(object):
    """
    An abstract base class for part tokens. Holds all token-level parameters
    of the part.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def parameters(self):
        """
        return list of parameters
        """
        pass

    @abstractmethod
    def lbs(self, eps=1e-4):
        """
        return list of lower bounds for parameters
        """
        pass

    @abstractmethod
    def ubs(self, eps=1e-4):
        """
        return list of upper bounds for parameters
        """
        pass

    def train(self):
        """
        makes params require grad
        """
        for param in self.parameters():
            param.requires_grad_(True)

    def eval(self):
        """
        makes params require no grad
        """
        for param in self.parameters():
            param.requires_grad_(False)

    def to(self, device):
        """
        moves parameters to device
        TODO
        """
        pass


class StrokeToken(PartToken):
    """
    Stroke tokens hold all token-level parameters of the stroke.

    Parameters
    ----------
    shapes : (ncpt, 2, nsub) tensor
        shapes tokens
    invscales : (nsub,) tensor
        invscales tokens
    xlim : (2,) tensor
        [lower, upper] bound for x dimension. Needed for position optimization
    ylim : (2,) tensor
        [lower, upper] bound for y dimension. Needed for position optimization
    """
    def __init__(self, shapes, invscales, xlim, ylim):
        super(StrokeToken, self).__init__()
        self.shapes = shapes
        self.invscales = invscales
        self.position = None

        # for image bounds
        self.xlim = xlim
        self.ylim = ylim

    @property
    def motor(self):
        """
        TODO
        """
        assert self.position is not None
        motor, _ = vanilla_to_motor(
            self.shapes, self.invscales, self.position
        )

        return motor

    @property
    def motor_spline(self):
        """
        TODO
        """
        assert self.position is not None
        _, motor_spline = vanilla_to_motor(
            self.shapes, self.invscales, self.position
        )

        return motor_spline

    def parameters(self):
        """
        Returns a list of parameters that can be optimized via gradient descent.

        Returns
        -------
        parameters : list
            optimizable parameters
        """
        parameters = [self.shapes, self.invscales, self.position]

        return parameters

    def lbs(self, eps=1e-4):
        """
        Returns a list of lower bounds for each of the optimizable parameters.

        Parameters
        ----------
        eps : float
            tolerance for constrained optimization

        Returns
        -------
        lbs : list
            lower bound for each parameter
        """
        bounds = torch.stack([self.xlim, self.ylim])
        lbs = [None, torch.full(self.invscales.shape, eps), bounds[:,0]+eps]

        return lbs

    def ubs(self, eps=1e-4):
        """
        Returns a list of upper bounds for each of the optimizable parameters.

        Parameters
        ----------
        eps : float
            tolerance for constrained optimization

        Returns
        -------
        ubs : list
            upper bound for each parameter
        """
        bounds = torch.stack([self.xlim, self.ylim])
        ubs = [None, None, bounds[:,1]-eps]

        return ubs


def vanilla_to_motor(shapes, invscales, first_pos, neval=200):
    """
    Create the fine-motor trajectory of a stroke (denoted 'f()' in pseudocode)
    with 'nsub' sub-strokes.
    Reference: BPL/classes/Stroke.m (lines 203-238)

    :param shapes: [(ncpt,2,nsub) tensor] spline points in normalized space
    :param invscales: [(nsub,) tensor] inverse scales for each sub-stroke
    :param first_pos: [(2,) tensor] starting location of stroke
    :param neval: [int] number of evaluations to use for each motor
                    trajectory
    :return:
        motor: [(nsub,neval,2) tensor] fine motor sequence
        motor_spline: [(ncpt,2,nsub) tensor] fine motor sequence in spline space
    """
    for elt in [shapes, invscales, first_pos]:
        assert elt is not None
        assert isinstance(elt, torch.Tensor)
    assert len(shapes.shape) == 3
    assert shapes.shape[1] == 2
    assert len(invscales.shape) == 1
    assert first_pos.shape == torch.Size([2])
    ncpt, _, nsub = shapes.shape
    motor = torch.zeros(nsub, neval, 2, dtype=torch.float)
    motor_spline = torch.zeros_like(shapes, dtype=torch.float)
    previous_pos = first_pos
    for i in range(nsub):
        # re-scale the control points
        shapes_scaled = invscales[i]*shapes[:,:,i]
        # get trajectories from b-spline
        traj = splines.get_stk_from_bspline(shapes_scaled, neval)
        # reposition; shift by offset
        offset = traj[0] - previous_pos
        motor[i] = traj - offset
        motor_spline[:,:,i] = shapes_scaled - offset
        # update previous_pos to be last position of current traj
        previous_pos = motor[i,-1]

    return motor, motor_spline