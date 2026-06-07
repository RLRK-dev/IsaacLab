"""
THREAD: Tactile-Hierarchical Reinforcement with Embodied Attention for Deformables
===================================================================================

This package implements the THREAD framework for dexterous cable manipulation
using Isaac Lab 2.3.0 and RSL-RL.

Main Components:
    - envs/: Isaac Lab environment definitions
    - train.py: Training script
    - eval.py: Evaluation script

Usage:
    # Training
    python train.py --num_envs 256 --max_iterations 50000
    
    # Evaluation
    python eval.py --checkpoint logs/THREAD_HookHanging/checkpoint_50000.pt

Author: THREAD Research Team
Date: December 2025
"""

__version__ = "1.0.0"
__author__ = "THREAD Research Team"

from pathlib import Path

# Package root directory
PACKAGE_DIR = Path(__file__).parent

# Default paths
DEFAULT_LOG_DIR = PACKAGE_DIR / "logs"
DEFAULT_CHECKPOINT_DIR = PACKAGE_DIR / "checkpoints"
