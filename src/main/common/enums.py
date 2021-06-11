from enum import Enum


class WindowType(Enum):
    hann = "hann"
    hamming = "hamming"


class TransientDetectionType(Enum):
    NONE = 0
    PERCUSSIVE = 1
    COMPOUND = 2
    HIGH_FREQ = 3

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        return NotImplemented


class PhaseResetType(Enum):
    FULL_RANGE = 0
    BAND_LIMITED = 1

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        return NotImplemented
