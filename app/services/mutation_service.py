"""
Mutation Service - Handle node/edge mutations and downstream recomputation
"""

from typing import Optional, List
from app.schemas.scenario import CausalGraphSchema, CausalNodeSchema, CausalEdgeSchema
from app.services.graph_service import GraphService


class MutationService:
    """Service for mutating causal graphs and recomputing downstream effects"""

    @staticmethod
    def mutate_node(
        graph: CausalGraphSchema,
        node_id: str,
        new_label: Optional[str] = None,
        new_description: Optional[str] = None,
    ) -> CausalGraphSchema:
        """
        Mutate a node and mark descendants for recomputation.
        Returns new graph with mutation applied and changed nodes marked.
        """
        # Find the node to mutate
        node_to_mutate = None
        for node in graph.nodes:
            if node.id == node_id:
                node_to_mutate = node
                break

        if not node_to_mutate:
            raise ValueError(f"Node {node_id} not found")

        # Create new node with updated fields
        updated_node = node_to_mutate.copy(
            update={
                "label": new_label or node_to_mutate.label,
                "description": new_description or node_to_mutate.description,
                "is_user_modified": True,
            }
        )

        # Replace node in graph
        new_nodes = []
        for node in graph.nodes:
            if node.id == node_id:
                new_nodes.append(updated_node)
            else:
                new_nodes.append(node)

        # Mark descendants for recomputation
        descendants = GraphService.get_descendants(node_id, graph)
        for descendant_id in descendants:
            for i, node in enumerate(new_nodes):
                if node.id == descendant_id:
                    # In Phase 4, this will trigger LLM recomputation
                    # For now, just mark as modified
                    new_nodes[i] = node.copy(update={"is_user_modified": True})

        return CausalGraphSchema(nodes=new_nodes, edges=graph.edges)

    @staticmethod
    def add_node(
        graph: CausalGraphSchema,
        node: CausalNodeSchema,
    ) -> CausalGraphSchema:
        """Add a new node to the graph"""
        new_nodes = graph.nodes + [node]
        return CausalGraphSchema(nodes=new_nodes, edges=graph.edges)

    @staticmethod
    def add_edge(
        graph: CausalGraphSchema,
        edge: CausalEdgeSchema,
    ) -> CausalGraphSchema:
        """Add a new edge to the graph"""
        new_edges = graph.edges + [edge]
        return CausalGraphSchema(nodes=graph.nodes, edges=new_edges)
