from typing import Tuple
import numpy as np
import re

def is_integer_node(node_id):
    return re.fullmatch(r"\d+", node_id) is not None