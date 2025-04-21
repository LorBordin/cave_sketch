import re

def _is_integer_node(node_id):
    return re.fullmatch(r"\d+", node_id) is not None