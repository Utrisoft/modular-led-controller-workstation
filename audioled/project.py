import asyncio

from audioled.filtergraph import (FilterGraph, Updateable)


class Project(Updateable):

    def __init__(self, device=None):
        self.slots = [None for i in range(127)]
        self.activeSlotId = 0
        self._device = device

    def __cleanState__(self, stateDict):
        """
        Cleans given state dictionary from state objects beginning with _
        """
        for k in list(stateDict.keys()):
            if k.startswith('_'):
                stateDict.pop(k)
        return stateDict

    def __getstate__(self):
        """
        Default implementation of __getstate__ that deletes buffer, call __cleanState__ when overloading
        """
        state = self.__dict__.copy()
        self.__cleanState__(state)
        return state

    def setDevice(self, device):
        self._device = device

    def update(self, dt, event_loop=asyncio.get_event_loop()):
        """Update active FilterGraph
        
        Arguments:
            dt {[float]} -- Time since last update
        """
        if self.getSlot(self.activeSlotId) is not None:
            self.getSlot(self.activeSlotId).update(dt, event_loop)

    def process(self):
        """Process active FilterGraph
        """
        activeFilterGraph = self.getSlot(self.activeSlotId)
        if activeFilterGraph is not None:
            activeFilterGraph.process()
            if self._device is not None and activeFilterGraph.getLEDOutput() is not None:
                self._device.show(activeFilterGraph.getLEDOutput()._outputBuffer[0])

    def setFiltergraphForSlot(self, slotId, filterGraph):
        print("Set {} for slot {}".format(filterGraph, slotId))
        if isinstance(filterGraph, FilterGraph):
            self.slots[slotId] = filterGraph

    def activateSlot(self, slotId):
        self.activeSlotId = slotId
        print("Activate slot {} with {}".format(slotId, self.slots[slotId]))
        return self.getSlot(slotId)

    def getSlot(self, slotId):
        if self.slots[slotId] is None:
            self.slots[slotId] = FilterGraph()
        return self.slots[slotId]
