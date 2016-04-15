# -*- coding: utf-8 -*-
"""
    dummy.py
    ~~~~~~~~

    :copyright: (c) 2015-2016 by Satanowski.
    :license: GNU General Public License v3.0
"""

from .shop import Shop


class DummyShop(Shop):
    """Dummy shop class for testing."""
    URL = 'http://google.com'
    seq = [True, False, False, True, True]
    pos = 0

    def check(self):
        yield from self._get_page(self.URL)

        if DummyShop.pos == len(DummyShop.seq):
            DummyShop.pos = 0

        self.available = DummyShop.seq[DummyShop.pos]
        DummyShop.pos += 1
