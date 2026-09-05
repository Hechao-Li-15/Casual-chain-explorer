"""
Mocked data generators for testing and Phase 2 development
Generate realistic causal chains without requiring LLM calls
"""

from datetime import datetime
from typing import Optional, List
import uuid
from app.schemas.scenario import (
    CausalNodeSchema,
    CausalEdgeSchema,
    CausalGraphSchema,
)


class MockDataFactory:
    """Factory for generating mocked causal graphs"""

    # Node type templates
    NODE_TEMPLATES = {
        "geopolitical_event": {
            "icon": "🌍",
            "color": "#ff6b6b",
            "examples": [
                "Strait of Hormuz closes",
                "New US tariffs on semiconductors",
                "European bank collapses",
                "OPEC production cuts announced",
            ],
        },
        "macro_effect": {
            "icon": "📊",
            "color": "#ffd93d",
            "examples": [
                "Global supply chain disruption",
                "Inflation expectations rise",
                "Currency volatility increases",
                "Credit spreads widen",
            ],
        },
        "market_effect": {
            "icon": "📈",
            "color": "#6bcf7f",
            "examples": [
                "Energy stock prices rise",
                "Tech valuations compress",
                "Commodity futures spike",
                "Bond yields increase",
            ],
        },
        "financial_outcome": {
            "icon": "💰",
            "color": "#4d96ff",
            "examples": [
                "Oil exploration companies outperform",
                "Airlines face margin pressure",
                "Semiconductor shortage drives prices up",
                "Consumer discretionary underperforms",
            ],
        },
    }

    @staticmethod
    def generate_node(
        label: str,
        node_type: str,
        confidence: int = 80,
        parent_ids: Optional[List[str]] = None,
        scenario_id: str = "scenario_1",
    ) -> CausalNodeSchema:
        """Generate a single causal node"""
        time_horizons = ["immediate", "1 week", "2 weeks", "1 month", "3 months", "6 months"]
        assumptions_pool = [
            "Current geopolitical tensions persist",
            "No major countervailing policy response",
            "Market participants act rationally",
            "Capital flows freely",
            "Supply/demand dynamics unchanged",
            "No technological breakthrough occurs",
        ]

        return CausalNodeSchema(
            id=f"node_{uuid.uuid4().hex[:8]}",
            scenario_id=scenario_id,
            label=label,
            description=f"Event: {label}",
            node_type=node_type,
            confidence=confidence,
            time_horizon=time_horizons[min(len(time_horizons) - 1, confidence // 20)],
            financial_relevance=node_type in ["market_effect", "financial_outcome"],
            tradable_assets=(
                ["Oil", "Energy ETFs", "Airline stocks"]
                if "energy" in label.lower() or "oil" in label.lower()
                else None
            ),
            assumptions=assumptions_pool[:2],
            evidence=["News reports", "Market data"],
            is_user_modified=False,
            parent_ids=parent_ids or [],
        )

    @staticmethod
    def generate_edge(
        source_id: str,
        target_id: str,
        relationship: str = "causes",
        direction: str = "positive",
        confidence: int = 80,
    ) -> CausalEdgeSchema:
        """Generate a causal edge"""
        reasoning_pool = [
            f"{relationship} downstream effects",
            "Economic mechanism:",
            "Market participants respond to",
            "Chain of causality:",
        ]

        return CausalEdgeSchema(
            id=f"edge_{uuid.uuid4().hex[:8]}",
            source_node_id=source_id,
            target_node_id=target_id,
            relationship=relationship,
            direction=direction,
            confidence=confidence,
            reasoning=f"{reasoning_pool[0]} with {confidence}% confidence",
            assumptions=["Standard economic models apply"],
            evidence=["Empirical precedent"],
        )

    @staticmethod
    def hormuz_closure_scenario() -> CausalGraphSchema:
        """Mocked scenario: Strait of Hormuz closure"""
        nodes = [
            MockDataFactory.generate_node(
                label="Strait of Hormuz closes for 2 weeks",
                node_type="geopolitical_event",
                confidence=100,
                parent_ids=[],
            ),
            MockDataFactory.generate_node(
                label="Oil supply disruption expected",
                node_type="macro_effect",
                confidence=95,
                parent_ids=["node_0"],
            ),
            MockDataFactory.generate_node(
                label="Shipping costs increase 30-40%",
                node_type="market_effect",
                confidence=85,
                parent_ids=["node_1"],
            ),
            MockDataFactory.generate_node(
                label="Oil prices spike 15-20%",
                node_type="market_effect",
                confidence=80,
                parent_ids=["node_1"],
            ),
            MockDataFactory.generate_node(
                label="Energy companies' margins expand",
                node_type="financial_outcome",
                confidence=75,
                parent_ids=["node_3"],
            ),
            MockDataFactory.generate_node(
                label="Airlines face 5-10% margin compression",
                node_type="financial_outcome",
                confidence=70,
                parent_ids=["node_2"],
            ),
        ]

        # Reassign IDs for proper linking
        for i, node in enumerate(nodes):
            node.id = f"node_{i}"
            if i > 0:
                node.parent_ids = [f"node_{i-1}"] if i == 1 else []

        edges = [
            MockDataFactory.generate_edge("node_0", "node_1", direction="positive", confidence=95),
            MockDataFactory.generate_edge("node_1", "node_2", direction="positive", confidence=85),
            MockDataFactory.generate_edge("node_1", "node_3", direction="positive", confidence=80),
            MockDataFactory.generate_edge("node_3", "node_4", direction="positive", confidence=75),
            MockDataFactory.generate_edge("node_2", "node_5", direction="negative", confidence=70),
        ]

        return CausalGraphSchema(nodes=nodes, edges=edges)

    @staticmethod
    def ai_export_restrictions_scenario() -> CausalGraphSchema:
        """Mocked scenario: AI model export restrictions"""
        nodes = [
            MockDataFactory.generate_node(
                label="US restricts AI model exports",
                node_type="geopolitical_event",
                confidence=90,
                parent_ids=[],
            ),
            MockDataFactory.generate_node(
                label="Global AI development slows",
                node_type="macro_effect",
                confidence=85,
                parent_ids=["node_0"],
            ),
            MockDataFactory.generate_node(
                label="Demand for GPU chips remains elevated",
                node_type="market_effect",
                confidence=80,
                parent_ids=["node_1"],
            ),
            MockDataFactory.generate_node(
                label="Semiconductor companies benefit from sustained demand",
                node_type="financial_outcome",
                confidence=75,
                parent_ids=["node_2"],
            ),
            MockDataFactory.generate_node(
                label="Chip design companies lose export markets",
                node_type="financial_outcome",
                confidence=65,
                parent_ids=["node_1"],
            ),
        ]

        # Reassign IDs
        for i, node in enumerate(nodes):
            node.id = f"node_{i}"

        edges = [
            MockDataFactory.generate_edge("node_0", "node_1", direction="negative", confidence=85),
            MockDataFactory.generate_edge("node_1", "node_2", direction="mixed", confidence=80),
            MockDataFactory.generate_edge("node_2", "node_3", direction="positive", confidence=75),
            MockDataFactory.generate_edge("node_1", "node_4", direction="negative", confidence=65),
        ]

        return CausalGraphSchema(nodes=nodes, edges=edges)

    @staticmethod
    def photonic_chips_scenario() -> CausalGraphSchema:
        """Mocked scenario: Photonic chips breakthrough"""
        nodes = [
            MockDataFactory.generate_node(
                label="Photonic chip technology matures",
                node_type="geopolitical_event",
                confidence=85,
                parent_ids=[],
            ),
            MockDataFactory.generate_node(
                label="Data center interconnect speeds increase 10x",
                node_type="macro_effect",
                confidence=80,
                parent_ids=["node_0"],
            ),
            MockDataFactory.generate_node(
                label="Power consumption per computation drops 40%",
                node_type="market_effect",
                confidence=75,
                parent_ids=["node_1"],
            ),
            MockDataFactory.generate_node(
                label="Data center capex budgets decrease",
                node_type="market_effect",
                confidence=70,
                parent_ids=["node_2"],
            ),
            MockDataFactory.generate_node(
                label="Photonic chip manufacturers see revenue surge",
                node_type="financial_outcome",
                confidence=80,
                parent_ids=["node_0"],
            ),
            MockDataFactory.generate_node(
                label="Traditional semiconductor companies face margin pressure",
                node_type="financial_outcome",
                confidence=65,
                parent_ids=["node_1"],
            ),
        ]

        # Reassign IDs
        for i, node in enumerate(nodes):
            node.id = f"node_{i}"

        edges = [
            MockDataFactory.generate_edge("node_0", "node_1", direction="positive", confidence=80),
            MockDataFactory.generate_edge("node_1", "node_2", direction="positive", confidence=75),
            MockDataFactory.generate_edge("node_2", "node_3", direction="negative", confidence=70),
            MockDataFactory.generate_edge("node_0", "node_4", direction="positive", confidence=80),
            MockDataFactory.generate_edge("node_1", "node_5", direction="negative", confidence=65),
        ]

        return CausalGraphSchema(nodes=nodes, edges=edges)

    @staticmethod
    def fed_rate_cuts_scenario() -> CausalGraphSchema:
        """Mocked scenario: Fed begins emergency rate cuts"""
        nodes = [
            MockDataFactory.generate_node(
                label="Federal Reserve cuts rates by 200 bps",
                node_type="geopolitical_event",
                confidence=100,
                parent_ids=[],
            ),
            MockDataFactory.generate_node(
                label="Real interest rates turn negative",
                node_type="macro_effect",
                confidence=95,
                parent_ids=["node_0"],
            ),
            MockDataFactory.generate_node(
                label="Inflation expectations surge",
                node_type="market_effect",
                confidence=85,
                parent_ids=["node_1"],
            ),
            MockDataFactory.generate_node(
                label="Growth-oriented equities outperform",
                node_type="financial_outcome",
                confidence=80,
                parent_ids=["node_1"],
            ),
            MockDataFactory.generate_node(
                label="Bond yields collapse",
                node_type="market_effect",
                confidence=90,
                parent_ids=["node_0"],
            ),
            MockDataFactory.generate_node(
                label="Tech stocks surge on lower discount rates",
                node_type="financial_outcome",
                confidence=75,
                parent_ids=["node_4"],
            ),
        ]

        # Reassign IDs
        for i, node in enumerate(nodes):
            node.id = f"node_{i}"

        edges = [
            MockDataFactory.generate_edge("node_0", "node_1", direction="negative", confidence=95),
            MockDataFactory.generate_edge("node_1", "node_2", direction="positive", confidence=85),
            MockDataFactory.generate_edge("node_1", "node_3", direction="positive", confidence=80),
            MockDataFactory.generate_edge("node_0", "node_4", direction="negative", confidence=90),
            MockDataFactory.generate_edge("node_4", "node_5", direction="positive", confidence=75),
        ]

        return CausalGraphSchema(nodes=nodes, edges=edges)

    @staticmethod
    def get_scenario_by_event(root_event: str) -> Optional[CausalGraphSchema]:
        """
        Return a mocked causal graph based on the root event.
        Matches keywords to predefined scenarios.
        """
        root_lower = root_event.lower()

        if ("hormuz" in root_lower or "strait" in root_lower) and ("open" in root_lower or "reopen" in root_lower):
            return MockDataFactory.hormuz_opening_scenario()
        elif "hormuz" in root_lower or "strait" in root_lower:
            return MockDataFactory.hormuz_closure_scenario()
        elif "export restrict" in root_lower or "ai model" in root_lower:
            return MockDataFactory.ai_export_restrictions_scenario()
        elif "photonic" in root_lower or "chip" in root_lower:
            return MockDataFactory.photonic_chips_scenario()
        elif "fed" in root_lower or "rate cut" in root_lower:
            return MockDataFactory.fed_rate_cuts_scenario()
        else:
            # Generic fallback: generate a simple 3-node chain
            return MockDataFactory._generate_generic_chain(root_event)

    @staticmethod
    def hormuz_opening_scenario() -> CausalGraphSchema:
        """Mocked scenario for a reopening, with easing downstream pressure."""
        graph = MockDataFactory.hormuz_closure_scenario()
        labels = [
            "Strait of Hormuz opens",
            "Shipping disruption risk falls",
            "Oil supply uncertainty falls",
            "Geopolitical risk premium falls",
            "Oil prices may decrease",
            "Airline margins may improve",
        ]
        for node, label in zip(graph.nodes, labels):
            node.label = label
            node.description = f"Scenario implication: {label}"
            node.confidence = max(60, node.confidence - 5)
        for edge in graph.edges:
            edge.reasoning = "Reopening reduces transit and supply uncertainty along the chain"
            edge.evidence = ["Model-suggested evidence"]
        return graph

    @staticmethod
    def _generate_generic_chain(root_event: str) -> CausalGraphSchema:
        """Generate a generic causal chain for any event"""
        nodes = [
            MockDataFactory.generate_node(
                label=root_event,
                node_type="geopolitical_event",
                confidence=100,
                parent_ids=[],
            ),
            MockDataFactory.generate_node(
                label="Economic impact becomes apparent",
                node_type="macro_effect",
                confidence=75,
                parent_ids=["node_0"],
            ),
            MockDataFactory.generate_node(
                label="Market participants adjust positions",
                node_type="market_effect",
                confidence=70,
                parent_ids=["node_1"],
            ),
            MockDataFactory.generate_node(
                label="Certain sectors may see trading opportunities",
                node_type="financial_outcome",
                confidence=60,
                parent_ids=["node_2"],
            ),
        ]

        for i, node in enumerate(nodes):
            node.id = f"node_{i}"

        edges = [
            MockDataFactory.generate_edge("node_0", "node_1", direction="positive", confidence=75),
            MockDataFactory.generate_edge("node_1", "node_2", direction="positive", confidence=70),
            MockDataFactory.generate_edge("node_2", "node_3", direction="positive", confidence=60),
        ]

        return CausalGraphSchema(nodes=nodes, edges=edges)
