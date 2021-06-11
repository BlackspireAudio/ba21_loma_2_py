import collections

import numpy as np


class AvgQueue:
    def __init__(self, size):
        self.size = size
        self.queue = collections.deque(np.zeros(size), maxlen=size)
        self.sum = 0
        self.avg = 0
        self.recalc_required = True

    def push_pop(self, val):
        self.recalc_required = True
        self.sum += val
        self.sum -= self.queue.pop()
        self.queue.appendleft(val)

    def get_avg(self):
        if self.recalc_required:
            self.avg = self.sum / self.size
            self.recalc_required = False
        return self.avg
