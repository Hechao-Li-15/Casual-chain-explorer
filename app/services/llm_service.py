"""
LLM Service - abstraction for mocked and OpenAI-backed causal generation.
"""

import json
import os
import re
from typing import Optional

from openai import AsyncOpenAI

from app.schemas.scenario import CausalGraphSchema
from app.services.mock_data import MockDataFactory


class LLMService:
    """Abstract interface for LLM integration."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"
        self.mock_data = MockDataFactory()
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def _call_openai(self, prompt: str) -> str:
        """Call the OpenAI chat completion API and return raw content."""
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured")

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate causal graphs in strict JSON. "
                        "Return only a JSON object with a 'nodes' array and an 'edges' array. "
                        "Each node must contain id, scenario_id, label, description, node_type, "
                        "confidence, time_horizon, financial_relevance, tradable_assets, "
                        "assumptions, evidence, is_user_modified, parent_ids. "
                        "Each edge must contain id, source_node_id, target_node_id, relationship, "
                        "direction, confidence, reasoning, assumptions, evidence."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned empty content")
        return content

    def _parse_graph_payload(self, payload: str) -> CausalGraphSchema:
        """Parse raw LLM JSON and validate it into the app model."""
        cleaned = payload.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        data = json.loads(cleaned)
        if not isinstance(data, dict) or "nodes" not in data or "edges" not in data:
            raise ValueError("OpenAI response did not contain a valid causal graph")

        return CausalGraphSchema.model_validate(data)

    async def generate_causal_chain(
        self, root_event: str, target_event: Optional[str] = None
    ) -> CausalGraphSchema:
        """Generate a causal chain from root_event to target_event."""
        if self.client:
            prompt = (
                f"Create a causal graph for '{root_event}' with 4 to 8 nodes. "
                f"Use intermediate causal mechanisms instead of jumping to an asset outcome. "
                f"Target event: {target_event or 'None'}. Include uncertainty, time horizons, "
                "assumptions, possible disconfirming factors, and distinguish inference from fact. "
                "Evidence must be exactly 'Model-suggested evidence' unless supplied by the user."
            )
            for _ in range(2):
                try:
                    payload = await self._call_openai(prompt)
                    return self._parse_graph_payload(payload)
                except Exception:
                    continue

        graph = MockDataFactory.get_scenario_by_event(root_event)
        if not graph:
            graph = MockDataFactory._generate_generic_chain(root_event)
        return graph

    async def validate_thesis(self, event_a: str, event_b: str) -> dict:
        """Validate whether event_a can lead to event_b."""
        graph = await self.generate_causal_chain(event_a)

        event_b_lower = event_b.lower()
        matching_nodes = [n for n in graph.nodes if event_b_lower in n.label.lower()]

        if matching_nodes:
            return {
                "verdict": "plausible",
                "explanation": f"Causal path exists from '{event_a}' to '{event_b}'",
                "confidence": 70,
                "path_length": len(matching_nodes),
            }

        return {
            "verdict": "weak",
            "explanation": f"No direct causal path found from '{event_a}' to '{event_b}'",
            "confidence": 30,
            "path_length": 0,
        }

    async def generate_trade_thesis(self, causal_graph: CausalGraphSchema) -> dict:
        """Generate a trade thesis from a causal graph."""
        financial_outcomes = [
            n for n in causal_graph.nodes if n.node_type == "financial_outcome"
        ]

        if not financial_outcomes:
            return {
                "thesis": "No clear tradable outcomes identified",
                "expected_effect": "Unclear",
                "potential_trade": "None",
                "confidence": 0,
            }

        outcome = financial_outcomes[0]
        return {
            "thesis": f"Based on causal chain, {outcome.label}",
            "expected_effect": outcome.description,
            "potential_trade": f"Position for {outcome.label}",
            "confidence": outcome.confidence,
        }
