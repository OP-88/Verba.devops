#!/usr/bin/env python3
"""
Fix numpy dtype compatibility issues
"""

import numpy as np

# Set default float type to float32 globally
np.set_printoptions(suppress=True)

# Monkey patch to ensure float32 compatibility
original_array = np.array

def fixed_array(*args, **kwargs):
    if 'dtype' not in kwargs and len(args) > 0:
        if isinstance(args[0], (list, tuple)) and all(isinstance(x, (int, float)) for x in args[0]):
            kwargs['dtype'] = np.float32
    return original_array(*args, **kwargs)

np.array = fixed_array

print("✅ NumPy dtype compatibility fix applied")
