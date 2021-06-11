import numpy as np


def princarg2(phase):
    return ((phase + np.pi) % (-2 * np.pi)) + np.pi

def princarg3(phase):
    return ((phase + np.pi) % (2 * np.pi)) - np.pi


def princarg(phase):
    return phase - 2 * np.pi * np.round(phase / (2*np.pi)).astype(int)
