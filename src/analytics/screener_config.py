"""
Screener Configuration and Schema Module.
Defines data structures for filtering criteria, evaluation operators,
and screening configuration presets for Nifty 100 stocks.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum


class FilterOperator(Enum):
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    EQUALS = "=="
    BETWEEN = "BETWEEN"
    IN_LIST = "IN"


@dataclass
class FilterCriterion:
    """Represents a single metric filtering rule."""

    metric_name: str
    operator: FilterOperator
    value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    weight: float = 1.0
    description: str = ""

    def evaluate(self, val: Any) -> bool:
        """Evaluates a single numeric or categorical value against criterion."""
        if val is None:
            return False

        try:
            val_float = float(val)
        except (ValueError, TypeError):
            val_float = None

        if self.operator == FilterOperator.GREATER_THAN:
            return val_float is not None and val_float > self.value
        elif self.operator == FilterOperator.GREATER_EQUAL:
            return val_float is not None and val_float >= self.value
        elif self.operator == FilterOperator.LESS_THAN:
            return val_float is not None and val_float < self.value
        elif self.operator == FilterOperator.LESS_EQUAL:
            return val_float is not None and val_float <= self.value
        elif self.operator == FilterOperator.EQUALS:
            return val == self.value
        elif self.operator == FilterOperator.BETWEEN:
            if val_float is None:
                return False
            low = self.min_value if self.min_value is not None else float("-inf")
            high = self.max_value if self.max_value is not None else float("inf")
            return low <= val_float <= high
        elif self.operator == FilterOperator.IN_LIST:
            if isinstance(self.value, (list, set, tuple)):
                return val in self.value
            return val == self.value
        return False


@dataclass
class ScreenerConfig:
    """Complete screener query configuration container."""

    name: str
    description: str
    criteria: List[FilterCriterion] = field(default_factory=list)
    handle_financials_de: bool = True
    handle_zero_debt_icr: bool = True
    sort_by: str = "composite_score"
    ascending: bool = False
    limit: Optional[int] = None

    def add_criterion(self, criterion: FilterCriterion) -> None:
        self.criteria.append(criterion)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "handle_financials_de": self.handle_financials_de,
            "handle_zero_debt_icr": self.handle_zero_debt_icr,
            "sort_by": self.sort_by,
            "ascending": self.ascending,
            "limit": self.limit,
            "criteria_count": len(self.criteria),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScreenerConfig":
        criteria = []
        for c in data.get("criteria", []):
            op = (
                FilterOperator(c["operator"])
                if isinstance(c["operator"], str)
                else c["operator"]
            )
            criteria.append(
                FilterCriterion(
                    metric_name=c["metric_name"],
                    operator=op,
                    value=c.get("value"),
                    min_value=c.get("min_value"),
                    max_value=c.get("max_value"),
                    weight=c.get("weight", 1.0),
                    description=c.get("description", ""),
                )
            )
        return cls(
            name=data.get("name", "Custom Screener"),
            description=data.get("description", ""),
            criteria=criteria,
            handle_financials_de=data.get("handle_financials_de", True),
            handle_zero_debt_icr=data.get("handle_zero_debt_icr", True),
            sort_by=data.get("sort_by", "composite_score"),
            ascending=data.get("ascending", False),
            limit=data.get("limit"),
        )

    @classmethod
    def from_json(cls, json_path: str) -> "ScreenerConfig":
        import json

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "ScreenerConfig":
        import yaml

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def load_all_from_yaml(cls, yaml_path: str) -> List["ScreenerConfig"]:
        import yaml

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if "presets" in data:
            return [cls.from_dict(p) for p in data["presets"]]
        return [cls.from_dict(data)]
