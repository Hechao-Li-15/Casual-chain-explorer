"""
Scenario API Routes
Endpoints for scenario management, generation, mutation, and analysis.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.scenario import (
    ScenarioCreateSchema,
    ScenarioSchema,
    ScenarioVersionSchema,
    MutateNodeSchema,
    CausalGraphSchema,
    ValidationResultSchema,
    TradeThesisSchema,
)
from app.schemas.requests import (
    GenerateCausalChainRequestSchema,
    ValidateThesisRequestSchema,
    AddCompetingEventRequestSchema,
)
from app.repositories.scenario_repo import scenario_repo
from app.services.llm_service import LLMService
from app.services.graph_service import GraphService
from app.services.mutation_service import MutationService
from app.services.thesis_service import ThesisService

router = APIRouter()

# Initialize services
llm_service = LLMService()
graph_service = GraphService()
mutation_service = MutationService()
thesis_service = ThesisService()


@router.post("/scenarios", response_model=ScenarioSchema)
async def create_scenario(data: ScenarioCreateSchema):
    """Create a new scenario"""
    return scenario_repo.create_scenario(data)


@router.get("/scenarios/{scenario_id}", response_model=ScenarioSchema)
async def get_scenario(scenario_id: str):
    """Retrieve a scenario"""
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("/scenarios/{scenario_id}/generate", response_model=CausalGraphSchema)
async def generate_causal_chain(scenario_id: str):
    """
    Generate a causal chain for a scenario.
    In Phase 2, generates mocked causal chains based on event keywords.
    In Phase 5+, integrates with OpenAI for real reasoning.
    """
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        # Use LLM service (mocked in Phase 2)
        graph = await llm_service.generate_causal_chain(
            scenario.root_event, scenario.target_event
        )

        # Update scenario with generated graph
        updated_scenario = scenario_repo.update_scenario(scenario_id, graph)
        scenario_repo.create_version(scenario_id, "Initial causal graph", graph)
        return updated_scenario.graph
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate causal chain: {str(e)}"
        )


@router.post("/scenarios/{scenario_id}/mutate", response_model=ScenarioVersionSchema)
async def mutate_node(scenario_id: str, data: MutateNodeSchema):
    """
    Mutate a node in the causal graph.
    Creates a new version and recomputes downstream effects.
    """
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        # Mutate the node
        mutated_graph = mutation_service.mutate_node(
            scenario.graph,
            data.node_id,
            new_label=data.new_label,
            new_description=data.new_description,
        )

        # In Phase 4+, would recompute downstream effects here
        # For now, just save the mutation

        # Create a new version
        mutation_desc = f"Modified node {data.node_id}"
        version = scenario_repo.create_version(scenario_id, mutation_desc, mutated_graph)

        return version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scenarios/{scenario_id}/validate", response_model=ValidationResultSchema)
async def validate_thesis(scenario_id: str, data: ValidateThesisRequestSchema):
    """
    Validate whether event_a can reasonably lead to event_b.
    In Phase 2, uses keyword-based matching on mocked causal chains.
    In Phase 5+, uses LLM to generate detailed causal analysis.
    """
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        # Use LLM service to generate graph and validate
        validation = await llm_service.validate_thesis(data.event_a, data.event_b)

        # Generate causal chain to extract path
        graph = await llm_service.generate_causal_chain(data.event_a, data.event_b)

        # Extract nodes in a causal path (simplified for Phase 2)
        from app.services.graph_service import GraphService

        causal_path_nodes = []
        if graph.nodes:
            # Use first 3 nodes as approximate path
            causal_path_nodes = graph.nodes[:3]

        result = ValidationResultSchema(
            verdict=validation.get("verdict", "weak"),
            explanation=validation.get("explanation", ""),
            causal_path=causal_path_nodes,
            weakest_link=(
                "Outcome probability" if causal_path_nodes else "No causal connection found"
            ),
            key_assumptions=["Market participants act rationally", "No major intervention"],
            alternative_explanations=["Alternative market dynamics"],
            confidence=validation.get("confidence", 50),
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/scenarios/{scenario_id}/thesis", response_model=TradeThesisSchema)
async def generate_thesis(scenario_id: str):
    """
    Generate a trade thesis from the current scenario.
    In Phase 2, generates a basic thesis from financial outcome nodes.
    In Phase 6+, uses LLM to generate detailed, nuanced thesis.
    """
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        # Generate or use existing graph
        if not scenario.graph.nodes:
            graph = await llm_service.generate_causal_chain(scenario.root_event)
        else:
            graph = scenario.graph

        # Generate thesis from graph
        thesis_data = await llm_service.generate_trade_thesis(graph)

        thesis = TradeThesisSchema(
            scenario_id=scenario_id,
            thesis=thesis_data.get("thesis", ""),
            expected_effect=thesis_data.get("expected_effect", ""),
            potential_trade=thesis_data.get("potential_trade", ""),
            catalysts=[scenario.root_event, "Confirmation of causal chain"],
            invalidation_conditions=[
                "Event does not materialize",
                "Counter-policy intervention",
            ],
            time_horizon="2-8 weeks",
            confidence=thesis_data.get("confidence", 60),
            risks=[
                "Model risk - causal assumptions may not hold",
                "Execution risk - market may already price event",
                "Tail risk - unforeseen second-order effects",
            ],
        )

        return thesis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thesis generation failed: {str(e)}")


@router.post("/scenarios/{scenario_id}/competing", response_model=ScenarioVersionSchema)
async def add_competing_event(scenario_id: str, data: AddCompetingEventRequestSchema):
    """
    Add a competing/alternative event as a new branch from a parent node.
    In Phase 4, creates a new node and edge.
    In Phase 5+, the LLM will recompute downstream effects for the new branch.
    """
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        # Find parent node
        parent_node = None
        for node in scenario.graph.nodes:
            if node.id == data.parent_node_id:
                parent_node = node
                break

        if not parent_node:
            raise ValueError(f"Parent node {data.parent_node_id} not found")

        # Create new node
        new_node_id = f"node_{len(scenario.graph.nodes) + 1}"
        from app.schemas.scenario import CausalNodeSchema

        new_node = CausalNodeSchema(
            id=new_node_id,
            scenario_id=scenario_id,
            label=data.label,
            description=data.description or "",
            node_type=parent_node.node_type,  # Same type as parent by default
            confidence=65,  # Conservative confidence for new node
            time_horizon=parent_node.time_horizon,
            financial_relevance=parent_node.financial_relevance,
            tradable_assets=parent_node.tradable_assets or [],
            assumptions=[],
            evidence=[],
            is_user_modified=True,
            parent_ids=[data.parent_node_id],
        )

        # Create new edge
        new_edge_id = f"edge_{len(scenario.graph.edges) + 1}"
        from app.schemas.scenario import CausalEdgeSchema

        new_edge = CausalEdgeSchema(
            id=new_edge_id,
            source_node_id=data.parent_node_id,
            target_node_id=new_node_id,
            relationship=f"Alternative: {data.label}",
            direction=data.direction,
            confidence=60,
            reasoning=data.description or "",
            assumptions=[],
            evidence=[],
        )

        # Add to graph
        updated_graph = CausalGraphSchema(
            nodes=[*scenario.graph.nodes, new_node],
            edges=[*scenario.graph.edges, new_edge],
        )

        # Create new version
        mutation_desc = f"Added alternative event: {data.label}"
        version = scenario_repo.create_version(scenario_id, mutation_desc, updated_graph)

        return version
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add competing event: {str(e)}")


@router.get("/scenarios/{scenario_id}/versions", response_model=list[ScenarioVersionSchema])
async def list_versions(scenario_id: str):
    """List all versions of a scenario"""
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return scenario_repo.get_versions(scenario_id)


@router.get("/scenarios/{scenario_id}/versions/{version_id}", response_model=ScenarioVersionSchema)
async def get_version(scenario_id: str, version_id: str):
    """Get a specific version of a scenario"""
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    version = scenario_repo.get_version(scenario_id, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return version


@router.post("/scenarios/{scenario_id}/versions/{version_id}/restore", response_model=ScenarioSchema)
async def restore_version(scenario_id: str, version_id: str):
    """Restore a historical scenario version to the current graph."""
    scenario = scenario_repo.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        restored = scenario_repo.restore_version(scenario_id, version_id)
        return restored
    except ValueError as exc:
        if "not found" in str(exc):
            raise HTTPException(status_code=404, detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
