from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CausalNodeSchema(BaseModel):
    """Schema for causal graph nodes"""

    id: str
    scenario_id: str
    label: str
    description: str
    node_type: str = Field(
        ..., description="Type: geopolitical_event, macro_effect, market_effect, financial_outcome"
    )
    confidence: int = Field(..., ge=0, le=100, description="Confidence 0-100")
    time_horizon: str = Field(..., description="Expected time horizon (e.g., '1 week')")
    financial_relevance: bool
    tradable_assets: Optional[List[str]] = None
    assumptions: List[str]
    evidence: List[str]
    is_user_modified: bool = False
    parent_ids: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "id": "node_1",
                "scenario_id": "scenario_1",
                "label": "Hormuz closes",
                "description": "Strait of Hormuz blockaded for 2 weeks",
                "node_type": "geopolitical_event",
                "confidence": 100,
                "time_horizon": "immediate",
                "financial_relevance": True,
                "assumptions": ["Geopolitical tensions escalate"],
                "evidence": ["Recent news reports"],
                "is_user_modified": False,
                "parent_ids": [],
            }
        }


class CausalEdgeSchema(BaseModel):
    """Schema for edges in causal graph"""

    id: str
    source_node_id: str
    target_node_id: str
    relationship: str
    direction: str = Field(..., description="positive, negative, or mixed")
    confidence: int = Field(..., ge=0, le=100)
    reasoning: str
    assumptions: List[str]
    evidence: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "id": "edge_1",
                "source_node_id": "node_1",
                "target_node_id": "node_2",
                "relationship": "causes",
                "direction": "positive",
                "confidence": 85,
                "reasoning": "Strait closure reduces oil supply",
                "assumptions": [],
                "evidence": [],
            }
        }


class CausalGraphSchema(BaseModel):
    """Complete causal graph"""

    nodes: List[CausalNodeSchema]
    edges: List[CausalEdgeSchema]


class ScenarioCreateSchema(BaseModel):
    """Request schema for creating a scenario"""

    title: str
    root_event: str
    target_event: Optional[str] = None
    mode: str = Field(..., description="validate or discover")


class ScenarioSchema(BaseModel):
    """Response schema for scenario"""

    id: str
    title: str
    root_event: str
    target_event: Optional[str] = None
    mode: str
    created_at: datetime
    current_version: int
    graph: CausalGraphSchema


class ScenarioVersionSchema(BaseModel):
    """Schema for scenario versions/branches"""

    id: str
    scenario_id: str
    version_number: int
    parent_version_id: Optional[str] = None
    mutation_description: str
    graph: CausalGraphSchema
    created_at: datetime


class MutateNodeSchema(BaseModel):
    """Request schema for mutating a node"""

    node_id: str
    new_label: Optional[str] = None
    new_description: Optional[str] = None


class ValidationResultSchema(BaseModel):
    """Response schema for validation"""

    verdict: str = Field(..., description="strong, plausible, weak, or unsupported")
    explanation: str
    causal_path: List[CausalNodeSchema]
    weakest_link: str
    key_assumptions: List[str]
    alternative_explanations: List[str]
    confidence: int


class TradeThesisSchema(BaseModel):
    """Response schema for trade thesis"""

    scenario_id: str
    thesis: str
    expected_effect: str
    potential_trade: str
    catalysts: List[str]
    invalidation_conditions: List[str]
    time_horizon: str
    confidence: int
    risks: List[str]
