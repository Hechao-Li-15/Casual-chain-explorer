"""
Thesis Service - Generate trade theses from causal graphs
"""

from app.schemas.scenario import CausalGraphSchema, TradeThesisSchema


class ThesisService:
    """Service for generating trade theses"""

    @staticmethod
    def generate_thesis(scenario_id: str, graph: CausalGraphSchema) -> TradeThesisSchema:
        """
        Generate a trade thesis from a causal graph.
        In Phase 6, this will call LLM to generate structured thesis.
        For now, returns mocked data.
        """
        return TradeThesisSchema(
            scenario_id=scenario_id,
            thesis="Mocked thesis in Phase 1",
            expected_effect="To be determined",
            potential_trade="To be determined",
            catalysts=[],
            invalidation_conditions=[],
            time_horizon="TBD",
            confidence=0,
            risks=[],
        )
