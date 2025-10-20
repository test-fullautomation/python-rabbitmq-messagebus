"""The package for standard messages.

Inspired by https://github.com/ros/std_msgs, this package defines messages
of primitive data types and multiarrays, that can be reused for many common
topics. If a more complex structural message is required, please add it to a
different package, e.g. taf_msgs.
"""
from .header import Header
from .msg import Msg
from .int32_msg import Int32Msg
from .uint32_msg import UInt32Msg
from .float32_msg import Float32Msg
from .float64_msg import Float64Msg
from .string_msg import StringMsg
from .dict_msg import DictMsg
