from .adafruit import Adafruit
from .botland import Botland
# from .element14 import Element14
from .pihut import Pihut
from .pimoroni import Pimoroni

shops = [
    Adafruit,
    Botland,
    # Element14, disabled since SSL errors, To be investigated
    Pihut,
    Pimoroni
]
