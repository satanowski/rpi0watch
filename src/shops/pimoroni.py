# -*- coding: utf-8 -*-
"""
    pimoroni.py
    ~~~~~~~~~~~

    :copyright: (c) 2015-2016 by Satanowski.
    :license: GNU General Public License v3.0
"""

from .shop import Shop, Product


class Pimoroni(Shop):
    URL = 'https://shop.pimoroni.com/products/raspberry-pi-zero'

    def check(self):
        raw = yield from self._get_page(self.URL)

        q = self.pq(raw or '<html/>')
        forms = q('form')

        self.available = 'in-stock' in ''.join(
            [f.attrib.get('class') for f in forms if
             f.attrib.get('action') == '/cart/add']
        )

        self.products = [Product('Pimoroni', self.URL, self.available)]
