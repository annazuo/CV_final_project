import argparse

from util import Args
from .classification import *
from .segmentation import *
from .experiments_linear import *
from .exp_resnet_hooks import *
from .densenet_channels import *


def get_model(model_args):
    model_args_ = model_args

    if isinstance(model_args, argparse.Namespace):
        model_args_ = Args(vars(model_args))

    return globals().copy()[model_args_.get("model")](model_args_)
