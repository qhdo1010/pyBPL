import numpy as np
from scipy.special import logsumexp
import networkx as nx

from ..parameters import ParametersBottomup
from .walker import Walker
from .walker_stroke import WalkerStroke
from . import util



class RandomWalker(Walker):
    """
    RandomWalker : produce a random walk on the graph skeleton.
    It is presumed the direction and order of the strokes doesn't
    matter, and this will be optimized later.
    """
    def __init__(self, graph, image, ps=None):
        """
        Parameters
        ----------
        graph : nx.Graph
            the (undirected) graph to walk on
        image : np.ndarray
            (H,W) original image in binary format
        ps : ParametersBottomup
            parameters for bottom-up methods
        """
        super().__init__(graph, image)
        if ps is None:
            ps = ParametersBottomup()
        self.ps = ps

    def sample(self):
        """
        Produce a sample from the random walk model
        """
        self.exp_wt_start = np.random.choice(self.ps.int_exp_wt)
        self.lmbda = np.random.choice(self.ps.int_lambda_soft)
        myns = float('inf')
        while myns > self.ps.max_len:
            walk = self.make()
            myns = len(walk)
        return walk

    def det_walk(self):
        """
        Produce a deterministic walk
        """
        self.exp_wt_start = 1000
        self.lmbda = 1000
        walk = self.make()
        return walk

    def make(self):
        """
        Make a random walk through the graph
        """
        assert hasattr(self, 'exp_wt_start')
        assert hasattr(self, 'lmbda')
        self.clear()
        self.add_singletons()
        if not self.complete:
            self.pen_up_down()
        while not self.complete:
            self.pen_angle_step()
        walk = self.S
        return walk

    def pen_up_down(self):
        """
        Place your pen down at an unvisited node,
        inversely proportional to the number of unvisited
        edges going from it.
        """
        new_ni, degree = self._available_nodes
        degree = np.asarray(degree, dtype=np.float32)
        logwts = self.exp_wt_start * np.log(1/degree)
        logwts = logwts - logsumexp(logwts)
        wts = np.exp(logwts)
        rindx = np.random.choice(len(wts), p=wts)
        stroke = WalkerStroke(new_ni[rindx])
        self.list_ws.append(stroke)
        if not self.complete:
            self.pen_simple_step()

    def pen_angle_step(self):
        """
        Angle move: select a step based on the angle
        from the current trajectory.
        """
        list_ei = self.get_moves()
        num_moves = len(list_ei)

        # if no available edges, pick up pen
        if num_moves == 0:
            self.pen_up_down()
            return

        # get angles for all move options
        angles = np.zeros(num_moves+1, dtype=np.float32)
        for i, edge in enumerate(list_ei):
            if self.is_visited(edge):
                # use default "faux_angle_repeat" for re-trace moves
                angles[i] = self.ps.faux_angle_repeat
            else:
                # use computed angles for new moves
                angles[i] = self._angle_for_move(edge)
        # extra move at end indicates "pen lift" option
        angles[-1] = self.ps.faux_angle_lift

        # select move stochastically
        rindx = self._action_via_angle(angles)
        if rindx == num_moves:
            self.pen_up_down()
        else:
            self.select_move(list_ei[rindx])

    def pen_simple_step(self):
        """
        Simple move: select a step uniformly at random
        from the set of new edges. Do not consider lifting
        the pen until you run out of new edges.
        """
        list_ei = self.get_new_moves()
        if len(list_ei) == 0:
            self.pen_up_down()
            return
        rindx = np.random.choice(len(list_ei))
        next_ei = list_ei[rindx]
        self.select_move(next_ei)

    def _action_via_angle(self, angles):
        """
        Given a vector of angles, compute move probabilities proportional
        to exp(-lambda*angle/180) and sample a move index
        """
        logp = -self.lmbda * angles / 180.
        logp = logp - logsumexp(logp)
        p = np.exp(logp)
        rindx = np.random.choice(len(p), p=p)
        return rindx

    def _angle_for_move(self, next_ei):
        """
        Compute angle for each move.
        """
        next_ni = next_ei[1] # next node

        # get current location (junction point)
        junct_pt = self.curr_pt
        # get ordered node list for the full candidate stroke
        list_ni = self.list_ws[-1].list_ni + [next_ni]
        list_ei = self.list_ws[-1].list_ei + [next_ei]
        # get stroke trajectory from ordered node list
        stroke = util.stroke_from_params(self.graph, list_ni, list_ei)
        # smooth the stroke
        stroke = util.fit_smooth_stk(stroke)

        # at the junction, isolate relevant segments of the stroke
        first_half, second_half = \
            util.split_by_junction(junct_pt, stroke, self.ps.rad_junction)
        angle = util.compute_angle(second_half, first_half, self.ps)

        # make sure there was no error in the angle calculation
        assert not np.isnan(angle)
        assert np.imag(angle) == 0

        return angle

    @property
    def _available_nodes(self):
        """
        Replacement for "pts_on_new_edges()" from BPL code.
        Find all nodes with at least one unvisited edge; return the
        node IDs and the "unvisited degree" values.
        """
        list_ni = []
        list_degree = []
        for ni in self.graph.nodes():
            # "unvisited degree" for each node is the total number of edges
            # minus the number of 'visited' edges
            degree_ni = self.graph.degree(ni) - self.graph.degree(ni, weight='visited')
            if degree_ni > 0:
                list_ni.append(ni)
                list_degree.append(degree_ni)

        return list_ni, list_degree
