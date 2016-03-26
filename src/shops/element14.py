# -*- coding: utf-8 -*-
"""
    element14.py
    ~~~~~~~~~~~~

    :copyright: (c) 2015-2016 by Satanowski.
    :license: GNU General Public License v3.0
"""

from .shop import Shop, Product


class Element14(Shop):
    URL = 'https://www.element14.com/community/docs/DOC-79263/l/introducing-'\
        'the-raspberry-pi-zero'


    def check(self):
        raw = yield from self._get_page(self.URL)
        q = self.pq(raw or '<html/>')
        self.available = True

        if 'Our service is temporarily unavailable' in q.html():
            self.available = False

        for span in q('table.jiveBorder span'):
            if span.text_content().strip() == 'Raspberry Pi Zero  SOLD OUT':
                self.available = False

        self.products = [Product('Element14', self.URL, self.available)]
