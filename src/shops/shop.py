# -*- coding: utf-8 -*-
"""
    shop.py
    ~~~~~~~

    :copyright: (c) 2015-2016 by Satanowski.
    :license: GNU General Public License v3.0
"""


from collections import namedtuple

from pyquery import PyQuery as pq
from utils import get_page

Product = namedtuple('Product', ['name', 'url', 'availability'])


class Shop():
    URL = ''

    def __init__(self):
        self.available = False
        self.products = []
        self.pq = pq
        self._get_page = get_page

    def check(self):
        """Run checking procedure."""
        raise NotImplementedError("Subclasses should implement this!")
