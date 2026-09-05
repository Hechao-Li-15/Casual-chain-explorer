"""
Graph Service - Core causal graph logic
Handles graph operations, layout, validation, and queries.
"""

from typing import List, Optional
from app.schemas.scenario import CausalNodeSchema, CausalEdgeSchema, CausalGraphSchema


class GraphService:
    """Service for causal graph operations"""

    @staticmethod
    def get_descendants(node_id: str, graph: CausalGraphSchema) -> List[str]:
        """
        Get all descendants of a node in the causal graph.
        Used to determine which nodes to recompute when one node changes.
        """
        descendants = set()

        def dfs(current_id: str):
            for edge in graph.edges:
                if edge.source_node_id == current_id:
                    target_id = edge.target_node_id
                    if target_id not in descendants:
                        descendants.add(target_id)
                        dfs(target_id)

        dfs(node_id)
        return list(descendants)

    @staticmethod
    def get_ancestors(node_id: str, graph: CausalGraphSchema) -> List[str]:
        """Get all ancestors of a node"""
        ancestors = set()

        def dfs(current_id: str):
            for edge in graph.edges:
                if edge.target_node_id == current_id:
                    source_id = edge.source_node_id
                    if source_id not in ancestors:
                        ancestors.add(source_id)
                        dfs(source_id)

        dfs(node_id)
        return list(ancestors)

    @staticmethod
    def find_path(source_id: str, target_id: str, graph: CausalGraphSchema) -> Optional[List[str]]:
        """
        Find a path from source node to target node.
        Used for validation mode to show the causal chain.
        """
        # BFS to find path
        from collections import deque

        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue:
            current, path = queue.popleft()
            if current == target_id:
                return path

            for edge in graph.edges:
                if edge.source_node_id == current:
                    next_node = edge.target_node_id
                    if next_node not in visited:
                        visited.add(next_node)
                        queue.append((next_node, path + [next_node]))

        return None
