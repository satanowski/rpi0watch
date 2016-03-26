# -*- coding: utf-8 -*-
"""
    botland.py
    ~~~~~~~~~~

    :copyright: (c) 2015-2016 by Satanowski.
    :license: GNU General Public License v3.0
"""

from .shop import Shop, Product


class Botland(Shop):
    URL = 'http://botland.com.pl/moduly-i-zestawy-raspberry-pi-2-i-3/5215-'\
        'raspberry-pi-zero-512mb-ram.html'

    def check(self):
        raw = yield from self._get_page(self.URL)
        q = self.pq(raw or '<html/>')
        button = q("#add_to_cart input")
        self.available = button and button[0].name == 'Submit'
        self.products = [Product(
            name='Botland',
            url=self.URL,
            availability=self.available
        )]
