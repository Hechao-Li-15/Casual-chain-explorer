"""
Scenario Repository - Persistence layer for scenarios
In Phase 1, this is a simple in-memory store.
In Phase 2+, will integrate with SQLite.
"""

from typing import Optional, List, Dict
import json
from datetime import datetime
from app.schemas.scenario import (
    ScenarioSchema,
    ScenarioCreateSchema,
    CausalGraphSchema,
    ScenarioVersionSchema,
)


class ScenarioRepository:
    """Repository for scenario persistence"""

    def __init__(self):
        # In-memory store for Phase 1
        self.scenarios: Dict[str, dict] = {}
        self.versions: Dict[str, List[dict]] = {}
        self.counter = 0

    def create_scenario(self, data: ScenarioCreateSchema) -> ScenarioSchema:
        """Create a new scenario"""
        self.counter += 1
        scenario_id = f"scenario_{self.counter}"

        scenario = {
            "id": scenario_id,
            "title": data.title,
            "root_event": data.root_event,
            "target_event": data.target_event,
            "mode": data.mode,
            "created_at": datetime.now(),
            "current_version": 1,
            "graph": {"nodes": [], "edges": []},
        }

        self.scenarios[scenario_id] = scenario
        self.versions[scenario_id] = []

        return ScenarioSchema(**scenario)

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioSchema]:
        """Retrieve a scenario by ID"""
        if scenario_id not in self.scenarios:
            return None

        return ScenarioSchema(**self.scenarios[scenario_id])

    def update_scenario(self, scenario_id: str, graph: CausalGraphSchema) -> ScenarioSchema:
        """Update a scenario's graph"""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")

        self.scenarios[scenario_id]["graph"] = graph.model_dump()
        return ScenarioSchema(**self.scenarios[scenario_id])

    def create_version(
        self,
        scenario_id: str,
        mutation_description: str,
        graph: CausalGraphSchema,
    ) -> ScenarioVersionSchema:
        """Create a new version/branch of a scenario"""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")

        version_number = len(self.versions[scenario_id]) + 1
        current_version = self.scenarios[scenario_id]["current_version"]
        parent_version_id = f"v{current_version}" if version_number > 1 else None

        version = {
            "id": f"v{version_number}",
            "scenario_id": scenario_id,
            "version_number": version_number,
            "parent_version_id": parent_version_id,
            "mutation_description": mutation_description,
            "graph": graph.model_dump(),
            "created_at": datetime.now(),
        }

        self.versions[scenario_id].append(version)
        self.scenarios[scenario_id]["graph"] = graph.model_dump()
        self.scenarios[scenario_id]["current_version"] = version_number

        return ScenarioVersionSchema(**version)

    def get_versions(self, scenario_id: str) -> List[ScenarioVersionSchema]:
        """Get all versions of a scenario"""
        if scenario_id not in self.versions:
            return []

        return [ScenarioVersionSchema(**v) for v in self.versions[scenario_id]]

    def get_version(self, scenario_id: str, version_id: str) -> Optional[ScenarioVersionSchema]:
        """Get a specific version"""
        for version in self.versions.get(scenario_id, []):
            if version["id"] == version_id:
                return ScenarioVersionSchema(**version)
        return None

    def restore_version(self, scenario_id: str, version_id: str) -> ScenarioSchema:
        """Restore a historical version of a scenario as the current graph."""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")

        if not self.versions.get(scenario_id):
            return ScenarioSchema(**self.scenarios[scenario_id])

        version = self.get_version(scenario_id, version_id)
        if version is None:
            raise ValueError(f"Version {version_id} not found")

        self.scenarios[scenario_id]["graph"] = version.graph.model_dump()
        self.scenarios[scenario_id]["current_version"] = version.version_number
        return ScenarioSchema(**self.scenarios[scenario_id])


# Global repository instance for Phase 1
scenario_repo = ScenarioRepository()
