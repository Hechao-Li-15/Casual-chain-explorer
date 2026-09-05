"""
Tests for mocked data generation and service integration
"""

import pytest
from app.services.mock_data import MockDataFactory
from app.services.llm_service import LLMService


class TestMockDataFactory:
    """Tests for mock data generation"""

    def test_generate_node(self):
        """Test generating a single node"""
        node = MockDataFactory.generate_node(
            label="Test Event",
            node_type="geopolitical_event",
            confidence=95,
        )

        assert node.label == "Test Event"
        assert node.node_type == "geopolitical_event"
        assert node.confidence == 95
        assert node.id.startswith("node_")
        assert node.time_horizon in [
            "immediate",
            "1 week",
            "2 weeks",
            "1 month",
            "3 months",
            "6 months",
        ]

    def test_generate_edge(self):
        """Test generating an edge"""
        edge = MockDataFactory.generate_edge(
            source_id="node_1",
            target_id="node_2",
            direction="positive",
            confidence=85,
        )

        assert edge.source_node_id == "node_1"
        assert edge.target_node_id == "node_2"
        assert edge.direction == "positive"
        assert edge.confidence == 85
        assert edge.id.startswith("edge_")

    def test_hormuz_closure_scenario(self):
        """Test Hormuz closure scenario generation"""
        graph = MockDataFactory.hormuz_closure_scenario()

        assert len(graph.nodes) == 6
        assert len(graph.edges) == 5
        assert graph.nodes[0].label == "Strait of Hormuz closes for 2 weeks"
        assert graph.nodes[0].node_type == "geopolitical_event"
        assert graph.nodes[0].confidence == 100

        # Check node IDs are properly reassigned
        for i, node in enumerate(graph.nodes):
            assert node.id == f"node_{i}"

    def test_ai_export_restrictions_scenario(self):
        """Test AI export restrictions scenario"""
        graph = MockDataFactory.ai_export_restrictions_scenario()

        assert len(graph.nodes) == 5
        assert len(graph.edges) == 4
        assert graph.nodes[0].node_type == "geopolitical_event"

    def test_photonic_chips_scenario(self):
        """Test photonic chips scenario"""
        graph = MockDataFactory.photonic_chips_scenario()

        assert len(graph.nodes) == 6
        assert len(graph.edges) == 5

    def test_fed_rate_cuts_scenario(self):
        """Test Fed rate cuts scenario"""
        graph = MockDataFactory.fed_rate_cuts_scenario()

        assert len(graph.nodes) == 6
        assert len(graph.edges) == 5

    def test_get_scenario_by_hormuz_event(self):
        """Test retrieving scenario by Hormuz keyword"""
        graph = MockDataFactory.get_scenario_by_event("Strait of Hormuz closes")
        assert graph is not None
        assert len(graph.nodes) > 0

    def test_get_scenario_by_ai_event(self):
        """Test retrieving scenario by AI keyword"""
        graph = MockDataFactory.get_scenario_by_event("AI model export restrictions")
        assert graph is not None
        assert len(graph.nodes) > 0

    def test_get_scenario_by_photonic_event(self):
        """Test retrieving scenario by photonic keyword"""
        graph = MockDataFactory.get_scenario_by_event("Photonic chips breakthrough")
        assert graph is not None
        assert len(graph.nodes) > 0

    def test_get_scenario_by_fed_event(self):
        """Test retrieving scenario by Fed keyword"""
        graph = MockDataFactory.get_scenario_by_event("Federal Reserve rate cuts")
        assert graph is not None
        assert len(graph.nodes) > 0

    def test_get_scenario_generic_fallback(self):
        """Test generic scenario generation for unknown events"""
        graph = MockDataFactory.get_scenario_by_event("Some random event")
        assert graph is not None
        assert len(graph.nodes) == 4  # Generic chain has 4 nodes
        assert len(graph.edges) == 3


class TestLLMServiceMocked:
    """Tests for LLM service with mocked data"""

    @pytest.fixture
    def llm_service(self):
        return LLMService(api_key=None)

    @pytest.mark.asyncio
    async def test_generate_causal_chain_hormuz(self, llm_service):
        """Test generating Hormuz causal chain"""
        graph = await llm_service.generate_causal_chain("Strait of Hormuz closes")

        assert graph is not None
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0
        assert graph.nodes[0].label == "Strait of Hormuz closes for 2 weeks"

    @pytest.mark.asyncio
    async def test_generate_causal_chain_generic(self, llm_service):
        """Test generating generic causal chain"""
        graph = await llm_service.generate_causal_chain("Some unusual event")

        assert graph is not None
        assert len(graph.nodes) == 4
        assert graph.nodes[0].label == "Some unusual event"

    @pytest.mark.asyncio
    async def test_validate_thesis_plausible(self, llm_service):
        """Test validating a plausible thesis"""
        result = await llm_service.validate_thesis(
            "Strait of Hormuz closes", "Oil prices increase"
        )

        assert result["verdict"] in ["strong", "plausible", "weak", "unsupported"]
        assert "explanation" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_validate_thesis_weak(self, llm_service):
        """Test validating a weak thesis"""
        result = await llm_service.validate_thesis(
            "Strait of Hormuz closes", "Penguins learn to swim"
        )

        assert result["verdict"] in ["weak", "unsupported"]

    @pytest.mark.asyncio
    async def test_generate_trade_thesis(self, llm_service):
        """Test generating a trade thesis"""
        graph = await llm_service.generate_causal_chain("Strait of Hormuz closes")
        thesis = await llm_service.generate_trade_thesis(graph)

        assert "thesis" in thesis
        assert "expected_effect" in thesis
        assert "potential_trade" in thesis
        assert "confidence" in thesis

    @pytest.mark.asyncio
    async def test_generate_causal_chain_with_openai_response(self, monkeypatch):
        """Test LLM parsing when an OpenAI JSON response is returned."""
        service = LLMService(api_key="sk-test")

        async def fake_call(prompt: str):
            return '{"nodes":[{"id":"node_0","scenario_id":"scenario_1","label":"Oil shock","description":"A supply shock","node_type":"macro_effect","confidence":90,"time_horizon":"1 month","financial_relevance":true,"tradable_assets":["Oil"],"assumptions":["Supply is constrained"],"evidence":["Market reports"],"is_user_modified":false,"parent_ids":[]},{"id":"node_1","scenario_id":"scenario_1","label":"Energy stocks rally","description":"Direct equity exposure","node_type":"financial_outcome","confidence":78,"time_horizon":"3 months","financial_relevance":true,"tradable_assets":["Energy ETFs"],"assumptions":["Demand remains strong"],"evidence":["ETF data"],"is_user_modified":false,"parent_ids":["node_0"]}],"edges":[{"id":"edge_0","source_node_id":"node_0","target_node_id":"node_1","relationship":"causes","direction":"positive","confidence":88,"reasoning":"Higher energy prices support energy equities","assumptions":[],"evidence":[]}]}'

        monkeypatch.setattr(service, "_call_openai", fake_call)

        graph = await service.generate_causal_chain("Oil shock")

        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.nodes[0].label == "Oil shock"
        assert graph.edges[0].direction == "positive"
