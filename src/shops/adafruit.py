# -*- coding: utf-8 -*-
"""
    adafruit.py
    ~~~~~~~~~~~

    :copyright: (c) 2015-2016 by Satanowski.
    :license: GNU General Public License v3.0
"""

from .shop import Shop, Product


class Adafruit(Shop):
    URL = 'https://www.adafruit.com/products/{}'
    VARIANTS = {
        2885: 'Only Pi',
        2817: 'Budget Pack',
        2816: 'StarterPack'
    }

    def check(self):
        self.products = []
        for var in self.VARIANTS:
            raw = yield from self._get_page(self.URL.format(var))
            q = self.pq(raw or '<html/>')
            av = 'OUT OF STOCK' not in [x.text_content() for x in
                                        q('#prod-stock .oos-header')]

            self.products.append(
                Product(
                    name='Adafruit: {}'.format(self.VARIANTS[var]),
                    url=self.URL.format(var),
                    availability=av
                )
            )

        self.available = any([prod.availability for prod in self.products])
