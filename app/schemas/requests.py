"""
Additional schemas for Phase 2 and beyond
"""

from pydantic import BaseModel, Field
from typing import Optional


class GenerateCausalChainRequestSchema(BaseModel):
    """Request to generate a causal chain"""

    root_event: str
    target_event: Optional[str] = None


class ValidateThesisRequestSchema(BaseModel):
    """Request to validate a thesis"""

    event_a: str
    event_b: str


class MutateNodeRequestSchema(BaseModel):
    """Request to mutate a node"""

    node_id: str
    new_label: Optional[str] = None
    new_description: Optional[str] = None
    new_confidence: Optional[int] = None


class AddCompetingEventRequestSchema(BaseModel):
    """Request body for adding a competing/alternative event."""
    parent_node_id: str = Field(..., description="ID of the parent node")
    label: str = Field(..., description="Label for the new event")
    description: Optional[str] = Field(None, description="Description of the competing event")
    direction: str = Field("mixed", description="Direction: positive, negative, or mixed")

    class Config:
        json_schema_extra = {
            "example": {
                "parent_node_id": "node_2",
                "label": "Energy crisis averted",
                "description": "Strategic reserves released, limiting price impact",
                "direction": "positive"
            }
        }
