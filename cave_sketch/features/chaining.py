# ruff: noqa: E501
from typing import Any, Dict, FrozenSet, List, Set


def chain_segments_by_type(lines: List[Dict[str, Any]]) -> Dict[str, List[List[List[float]]]]:
    # Group by type
    by_type: Dict[str, List[Dict[str, Any]]] = {}
    for line in lines:
        t = line.get("type", "unknown")
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(line)
        
    result: Dict[str, List[List[List[float]]]] = {}
    
    for t, segs in by_type.items():
        # Build an undirected graph, dedupe edges via frozenset({from_id, to_id})
        nodes: Dict[str, Dict[str, float]] = {}
        edges: Set[FrozenSet[str]] = set()
        
        for seg in segs:
            f = seg["from"]
            t_node = seg["to"]
            nodes[f["id"]] = {"lat": f["lat"], "lon": f["lon"]}
            nodes[t_node["id"]] = {"lat": t_node["lat"], "lon": t_node["lon"]}
            if f["id"] != t_node["id"]:
                edges.add(frozenset([f["id"], t_node["id"]]))
                
        # Build adjacency list
        adj: Dict[str, List[str]] = {n: [] for n in nodes}
        for e in edges:
            e_list = list(e)
            if len(e_list) == 2:
                u, v = e_list[0], e_list[1]
                adj[u].append(v)
                adj[v].append(u)
                
        # Find degrees
        degrees = {n: len(neighbors) for n, neighbors in adj.items()}
        
        visited_edges: Set[FrozenSet[str]] = set()
        polylines = []
        
        # Walk maximal chains starting at endpoints/junctions (degree != 2)
        start_nodes = [n for n, deg in degrees.items() if deg != 2]
        
        for start in start_nodes:
            for neighbor in adj[start]:
                edge = frozenset([start, neighbor])
                if edge in visited_edges:
                    continue
                    
                # Walk the chain
                chain = [start]
                curr = neighbor
                prev = start
                
                visited_edges.add(edge)
                
                while degrees[curr] == 2:
                    chain.append(curr)
                    # Find next node that is not prev
                    next_nodes = [n for n in adj[curr] if n != prev]
                    if not next_nodes:
                        break
                    next_n = next_nodes[0]
                    next_edge = frozenset([curr, next_n])
                    visited_edges.add(next_edge)
                    prev = curr
                    curr = next_n
                    
                chain.append(curr)
                polylines.append([[nodes[n]["lat"], nodes[n]["lon"]] for n in chain])
                
        # Emit leftover all-degree-2 components as closed polylines
        for n, deg in degrees.items():
            if deg == 2:
                unvisited = [nbr for nbr in adj[n] if frozenset([n, nbr]) not in visited_edges]
                if unvisited:
                    # Start a new closed loop
                    neighbor = unvisited[0]
                    edge = frozenset([n, neighbor])
                    
                    chain = [n]
                    curr = neighbor
                    prev = n
                    visited_edges.add(edge)
                    
                    while True:
                        chain.append(curr)
                        if curr == n:
                            break # completed the loop
                            
                        next_nodes = [nbr for nbr in adj[curr] if nbr != prev and frozenset([curr, nbr]) not in visited_edges]
                        if not next_nodes:
                            break
                            
                        next_n = next_nodes[0]
                        next_edge = frozenset([curr, next_n])
                        visited_edges.add(next_edge)
                        prev = curr
                        curr = next_n
                        
                    polylines.append([[nodes[node_id]["lat"], nodes[node_id]["lon"]] for node_id in chain])
                    
        result[t] = polylines
        
    return result
