# -*- coding: utf-8 -*-

def classFactory(iface):
    """
    Load QuickRoadNetworkPathAI class from file QuickRoadNetworkPathAI.py
    and return an instance of it.
    """
    from .QuickRoadNetworkPathAI import QuickRoadNetworkPathAI
    return QuickRoadNetworkPathAI(iface)
