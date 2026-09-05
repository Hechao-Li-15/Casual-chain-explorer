"""
Tests for core graph mutation logic
"""

import pytest
from app.schemas.scenario import (
    CausalNodeSchema,
    CausalEdgeSchema,
    CausalGraphSchema,
)
from app.services.graph_service import GraphService
from app.services.mutation_service import MutationService


@pytest.fixture
def sample_graph():
    """Create a sample causal graph for testing"""
    nodes = [
        CausalNodeSchema(
            id="n1",
            scenario_id="s1",
            label="Hormuz closes",
            description="Strait closes",
            node_type="geopolitical_event",
            confidence=100,
            time_horizon="1 week",
            financial_relevance=True,
            assumptions=["Geopolitical tension"],
            evidence=["News"],
            is_user_modified=False,
            parent_ids=[],
        ),
        CausalNodeSchema(
            id="n2",
            scenario_id="s1",
            label="Oil supply decreases",
            description="Oil supply affected",
            node_type="market_effect",
            confidence=90,
            time_horizon="1 week",
            financial_relevance=True,
            assumptions=[],
            evidence=[],
            is_user_modified=False,
            parent_ids=["n1"],
        ),
        CausalNodeSchema(
            id="n3",
            scenario_id="s1",
            label="Oil prices increase",
            description="Prices spike",
            node_type="financial_outcome",
            confidence=85,
            time_horizon="2 weeks",
            financial_relevance=True,
            assumptions=[],
            evidence=[],
            is_user_modified=False,
            parent_ids=["n2"],
        ),
    ]

    edges = [
        CausalEdgeSchema(
            id="e1",
            source_node_id="n1",
            target_node_id="n2",
            relationship="causes",
            direction="positive",
            confidence=90,
            reasoning="Strait closure reduces supply",
            assumptions=[],
            evidence=[],
        ),
        CausalEdgeSchema(
            id="e2",
            source_node_id="n2",
            target_node_id="n3",
            relationship="causes",
            direction="positive",
            confidence=85,
            reasoning="Lower supply increases prices",
            assumptions=[],
            evidence=[],
        ),
    ]

    return CausalGraphSchema(nodes=nodes, edges=edges)


def test_get_descendants(sample_graph):
    """Test finding descendants in causal graph"""
    descendants = GraphService.get_descendants("n1", sample_graph)
    assert "n2" in descendants
    assert "n3" in descendants
    assert len(descendants) == 2


def test_get_ancestors(sample_graph):
    """Test finding ancestors in causal graph"""
    ancestors = GraphService.get_ancestors("n3", sample_graph)
    assert "n2" in ancestors
    assert "n1" in ancestors
    assert len(ancestors) == 2


def test_find_path(sample_graph):
    """Test finding path between nodes"""
    path = GraphService.find_path("n1", "n3", sample_graph)
    assert path == ["n1", "n2", "n3"]

    # Test non-existent path
    path = GraphService.find_path("n3", "n1", sample_graph)
    assert path is None


def test_mutate_node(sample_graph):
    """Test mutating a node"""
    mutated = MutationService.mutate_node(
        sample_graph,
        "n2",
        new_label="Oil supply severely decreases",
    )

    # Find the mutated node
    updated_node = next(n for n in mutated.nodes if n.id == "n2")
    assert updated_node.label == "Oil supply severely decreases"
    assert updated_node.is_user_modified is True

    # Check that descendants are marked for recomputation
    descendant = next(n for n in mutated.nodes if n.id == "n3")
    assert descendant.is_user_modified is True

    # Check that ancestors are NOT marked
    ancestor = next(n for n in mutated.nodes if n.id == "n1")
    assert ancestor.is_user_modified is False


def test_add_node(sample_graph):
    """Test adding a new node"""
    new_node = CausalNodeSchema(
        id="n4",
        scenario_id="s1",
        label="Energy stocks outperform",
        description="Energy sector benefits",
        node_type="financial_outcome",
        confidence=70,
        time_horizon="3 weeks",
        financial_relevance=True,
        assumptions=[],
        evidence=[],
        is_user_modified=False,
        parent_ids=["n3"],
    )

    updated_graph = MutationService.add_node(sample_graph, new_node)
    assert len(updated_graph.nodes) == 4
    assert any(n.id == "n4" for n in updated_graph.nodes)


def test_add_edge(sample_graph):
    """Test adding a new edge"""
    new_node = CausalNodeSchema(
        id="n4",
        scenario_id="s1",
        label="Energy stocks outperform",
        description="Energy sector benefits",
        node_type="financial_outcome",
        confidence=70,
        time_horizon="3 weeks",
        financial_relevance=True,
        assumptions=[],
        evidence=[],
        is_user_modified=False,
        parent_ids=["n3"],
    )

    graph_with_node = MutationService.add_node(sample_graph, new_node)

    new_edge = CausalEdgeSchema(
        id="e3",
        source_node_id="n3",
        target_node_id="n4",
        relationship="causes",
        direction="positive",
        confidence=70,
        reasoning="Higher oil prices benefit energy stocks",
        assumptions=[],
        evidence=[],
    )

    updated_graph = MutationService.add_edge(graph_with_node, new_edge)
    assert len(updated_graph.edges) == 3
    assert any(e.id == "e3" for e in updated_graph.edges)
