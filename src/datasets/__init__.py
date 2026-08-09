"""
VLM Spatial Reasoning - Datasets

This package contains dataset loaders and processors for spatial reasoning tasks.
"""

from .vsr import load_vsr, load_vsr_splits, get_relation_frequency
from .site import load_site, load_site_splits, get_orientation_subset

__version__ = "0.1.0"
