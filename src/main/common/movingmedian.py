from heapq import heappush, heappop


class MovingMedian:
    def __init__(self, size, percentile=50.0):
        self.size = size
        self.get_percentile_index(percentile)
        self.heap = []
        for n in range(0, size):
            heappush(self.heap, 0)

    def get_percentile_index(self, percentile):
        self.percentile_index = int(self.size * percentile / 100)
        if self.percentile_index >= self.size:
            self.percentile_index = self.size - 1
        if self.percentile_index < 0:
            self.percentile_index = 0

    def put(self, number):
        heappop(self.heap)
        heappush(self.heap, number)

    def get(self):
        sortingHeap = self.heap
        sortingHeap.sort()
        return sortingHeap[self.percentile_index]
