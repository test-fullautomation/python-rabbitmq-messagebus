# wait_mode.py
from enum import Enum

class WaitMode(Enum):
    ALL_IN_GIVEN_ORDER   = 1
    ALL_IN_RANDOM_ORDER  = 2
    ANY_OF_GIVEN_MSGS    = 3
