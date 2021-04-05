import torch

from .type_dist import CharacterTypeDist
from .token_dist import CharacterTokenDist
from .image_dist import CharacterImageDist


class CharacterModel(object):
    """
    Sampling from and Scoring according to the graphical model. The model is
    defined as P(Type, Token, Image) = P(Type)*P(Token | Type)*P(Image | Token).
    The 3 component distributions P(Type), P(Token | Type), and P(Image | Token)
    are denoted 'type_dist', 'token_dist' and 'image_dist', respectively.
    """
    def __init__(self, lib):
        self.type_dist = CharacterTypeDist(lib)
        self.token_dist = CharacterTokenDist(lib)
        self.image_dist = CharacterImageDist(lib)

    def sample_type(self, k=None):
        return self.type_dist.sample_type(k)

    def score_type(self, ctype):
        return self.type_dist.score_type(ctype)

    def sample_token(self, ctype):
        return self.token_dist.sample_token(ctype)

    def score_token(self, ctype, ctoken):
        return self.token_dist.score_token(ctype, ctoken)

    def sample_image(self, ctoken):
        return self.image_dist.sample_image(ctoken)

    def score_image(self, ctoken, image):
        return self.image_dist.score_image(ctoken, image)

    def get_pimg(self, ctoken):
        return self.image_dist.get_pimg(ctoken)


def fit_image(im, lib):
    # Optimization would look something like this

    model = CharacterModel(lib)
    _type = model.sample_type()
    token = model.sample_token(_type)

    optimizer = torch.optim.Adam([{'params': _type.parameters()},
                                  {'params': token.parameters()}],
                                  lr=0.001)

    # Set requires_grad to True
    _type.train()
    token.train()

    for idx in range(100):
        optimizer.zero_grad()
        type_score = model.score_type(_type)
        token_score = model.score_token(_type,token)
        image_score = model.score_image(token,im)
        score = type_score + token_score + image_score
        loss = -score
        loss.backward()
        optimizer.step()

