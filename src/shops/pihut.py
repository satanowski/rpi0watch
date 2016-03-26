# -*- coding: utf-8 -*-
"""
    pihut.py
    ~~~~~~~~

    :copyright: (c) 2015-2016 by Satanowski.
    :license: GNU General Public License v3.0
"""

import json

from .shop import Shop, Product


class Pihut(Shop):
    URL = 'http://thepihut.com/collections/new-products/products/raspberry-pi'\
          '-zero.js'
    PROD_URL = 'https://thepihut.com/collections/raspberry-pi/products/'\
        'raspberry-pi-zero?variant={}'

    def check(self):
        self.products = []
        raw = yield from self._get_page(self.URL)
        j = json.loads(raw.decode() or '{}')

        for variant in j.get('variants', []):
            self.products.append(
                Product(
                    name='Pihut: {}'.format(variant['title']),
                    url=self.PROD_URL.format(variant['id']),
                    availability=variant['inventory_quantity'] > 0
                )
            )

        self.available = any([prod.availability for prod in self.products])
