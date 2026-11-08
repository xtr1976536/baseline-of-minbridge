from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError
import json


@dataclass
class Indicator:
    name: str
    desc: str
    formula: Optional[List[str]] = None
    dependencies: Optional[List[List[str]]] = None  # 依赖的指标名称列表


ReasoningType = Literal[
    "DirectRetrieval",
    "ArithmeticCalculation",
    "ComparativeReasoning",
    "StatisticalAggregation",
    "TemporalReasoning",
]


class MetaAttributes(BaseModel):
    currency: Optional[str] = Field(default=None, description="e.g., USD, CNY")
    scale: Optional[str] = Field(default=None, description="e.g., millions, billions")
    unit: Optional[str] = Field(default=None, description="e.g., percentage, ratio, days")


class Constraints(BaseModel):
    temporal_scope: Optional[str] = Field(default=None, description="e.g., 2024, 2023 Q4, Dec 31 2023")
    entity_scope: Optional[str] = Field(default=None, description="e.g., Company A, Group, Parent company of Company B")
    meta: MetaAttributes = Field(default_factory=MetaAttributes)


class Subgoal(BaseModel):
    metric: str = Field(default=None, description="metric mentioned in the question")
    constraints: Constraints


class OQAResult(BaseModel):
    reasoning_type: ReasoningType
    operator: str = Field(default=None,
                          description="Specific operator name, e.g., YoY_Growth_Rate, Difference, Ratio, Average")
    subgoals: List[Subgoal] = Field(default_factory=list)
    precision: str = Field(default="unknown", description="e.g., nearest integer, two decimal places")


class EvidenceItem(BaseModel):
    metric: str = Field(default=None, description="metric mentioned in the question")
    constraints: Constraints
    value: float
    context: str  # 证据的上下文
    confidence: float = Field(ge=0.0, le=1.0)  # 置信度


class EvidenceSeekingOutput(BaseModel):
    found: bool
    var_bindings: Dict[str, EvidenceItem] = Field(default_factory=dict)
    missing_vars: List[str] = Field(default_factory=list)
    notes: Optional[str] = None  # 歧义指标对齐说明


class PoTProgram(BaseModel):
    path_id: Optional[int] = 0
    indicator_name: str = ""
    formula_expr: str = ""
    required_vars: List[str] = Field(default_factory=list)
    program: str = ""
    reference_code: str = ""
    notes: Optional[str] = None


class PoTExecutionResult(BaseModel):
    path_id: Optional[int] = 0
    ok: bool = False
    value: Optional[float| Dict | Tuple|str] = None
    trace: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    program: str = ""


def extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # fallback: find first '{' and last '}'
        l = text.find("{")
        r = text.rfind("}")
        if l == -1 or r == -1 or r <= l:
            raise
        return json.loads(text[l: r + 1])


# =====================================================
# ProblemDecomposition 所需的数据结构
# =====================================================

from enum import Enum


class NodeStatus(str, Enum):
    """节点状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class PathStatus(str, Enum):
    """路径状态"""
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class IndicatorNode(BaseModel):
    """指标节点 - 用于构建分解树"""
    name: str = Field(description="指标名称")
    definition: str = Field(default="", description="指标定义")
    formula_expr: str = Field(default="", description="计算公式表达式")
    formula_code: str = Field(default="", description="计算公式代码")
    level: int = Field(default=0, description="在分解树中的层级")
    is_leaf: bool = Field(default=False, description="是否为叶子节点")
    aliases_zh: List[str] = Field(default_factory=list, description="中文别名")
    aliases_en: List[str] = Field(default_factory=list, description="英文别名")
    aliases_abbr: List[str] = Field(default_factory=list, description="缩写别名")
    children: List["IndicatorNode"] = Field(default_factory=list, description="子节点列表")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="节点状态")
    value: Optional[float] = Field(default=None, description="计算得到的值")

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        return {
            "name": self.name,
            "definition": self.definition,
            "formula_expr": self.formula_expr,
            "formula_code": self.formula_code,
            "level": self.level,
            "is_leaf": self.is_leaf,
            "aliases_zh": self.aliases_zh,
            "aliases_en": self.aliases_en,
            "aliases_abbr": self.aliases_abbr,
            "children": [child.to_dict() for child in self.children],
            "status": self.status.value,
            "value": self.value
        }


class DecompositionPath(BaseModel):
    """分解路径 - 代表一种计算方式"""
    path_id: int = Field(description="路径ID")
    root: IndicatorNode = Field(description="路径的根节点（目标指标）")
    formula_expr: str = Field(default="", description="该路径使用的公式表达式")
    formula_code: str = Field(default="", description="该路径使用的公式代码")
    total_nodes: int = Field(default=0, description="该路径的节点总数")
    max_depth: int = Field(default=0, description="该路径的最大深度")
    leaf_nodes: List[str] = Field(default_factory=list, description="叶子节点名称列表")
    status: PathStatus = Field(default=PathStatus.ACTIVE, description="路径状态")

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path_id": self.path_id,
            "root": self.root.to_dict(),
            "formula_expr": self.formula_expr,
            "formula_code": self.formula_code,
            "total_nodes": self.total_nodes,
            "max_depth": self.max_depth,
            "leaf_nodes": self.leaf_nodes,
            "status": self.status.value
        }


class DecompositionOutput(BaseModel):
    """分解算子的输出"""
    target_indicator: str = Field(description="目标指标名称")
    paths: List[DecompositionPath] = Field(default_factory=list, description="所有分解路径")
    success: bool = Field(default=True, description="分解是否成功")
    error_msg: str = Field(default="", description="错误信息")

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "target_indicator": self.target_indicator,
            "paths": [path.to_dict() for path in self.paths],
            "success": self.success,
            "error_msg": self.error_msg
        }

IndicatorNode.model_rebuild()