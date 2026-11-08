from typing import Annotated, Dict, List, TypedDict, Any, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from enum import Enum
import threading


class PathStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class CacheStatus(str, Enum):
    NOT_QUERIED = "not_queried"
    QUERYING = "querying"
    COMPLETED = "completed"


class CacheEntry(BaseModel):
    status: CacheStatus = CacheStatus.NOT_QUERIED
    value: Optional[float] = None
    unit: Optional[str] = None
    source: str = ""
    found: bool = False
    error_msg: str = ""

    class Config:
        arbitrary_types_allowed = True


class PathResult(BaseModel):
    path_id: str
    indicator_name: str = ""
    formula_expr: str = ""
    formula_index: int = 0
    depth: int = 0
    status: PathStatus = PathStatus.ACTIVE
    result: Optional[float|dict|tuple|str] = None
    node_results: Dict[str, float|dict|tuple|str] = Field(default_factory=dict)
    required_vars: List[str] = Field(default_factory=list)
    missing_vars: List[str] = Field(default_factory=list)
    child_paths: List[str] = Field(default_factory=list)
    error_msg: str = ""

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict:
        return {
            "path_id": self.path_id,
            "indicator_name": self.indicator_name,
            "formula_expr": self.formula_expr,
            "formula_index": self.formula_index,
            "depth": self.depth,
            "status": self.status.value,
            "result": self.result,
            "node_results": self.node_results,
            "required_vars": self.required_vars,
            "missing_vars": self.missing_vars,
            "child_paths": self.child_paths,
            "error_msg": self.error_msg
        }


class IndicatorTask(BaseModel):
    indicator_name: str
    constraints: Dict[str, Any] = Field(default_factory=dict)
    parent_path_id: Optional[str] = None
    depth: int = 0

    class Config:
        arbitrary_types_allowed = True


class ThreeStateCache:
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self._events: Dict[str, threading.Event] = {}
        self._global_lock = threading.Lock()

    def _get_lock(self, key: str) -> threading.Lock:
        with self._global_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def _get_event(self, key: str) -> threading.Event:
        with self._global_lock:
            if key not in self._events:
                self._events[key] = threading.Event()
            return self._events[key]

    def try_start_query(self, key: str) -> tuple:
        lock = self._get_lock(key)
        with lock:
            if key not in self._cache:
                self._cache[key] = CacheEntry(status=CacheStatus.QUERYING)
                self._events[key] = threading.Event()
                return (True, None)
            entry = self._cache[key]
            if entry.status == CacheStatus.COMPLETED:
                return (False, entry)
            elif entry.status == CacheStatus.QUERYING:
                return (False, None)
            else:
                self._cache[key].status = CacheStatus.QUERYING
                self._events[key] = threading.Event()
                return (True, None)

    def wait_for_result(self, key: str, timeout: float = 60.0) -> Optional[CacheEntry]:
        event = self._get_event(key)
        event.wait(timeout=timeout)
        return self._cache.get(key)

    def complete_query(self, key: str, value: Optional[float], found: bool,
                       unit: str = None, source: str = "", error_msg: str = ""):
        lock = self._get_lock(key)
        with lock:
            self._cache[key] = CacheEntry(
                status=CacheStatus.COMPLETED,
                value=value,
                unit=unit,
                source=source,
                found=found,
                error_msg=error_msg
            )
            event = self._get_event(key)
            event.set()

    def get(self, key: str) -> Optional[CacheEntry]:
        return self._cache.get(key)

    def has_completed(self, key: str) -> bool:
        entry = self._cache.get(key)
        return entry is not None and entry.status == CacheStatus.COMPLETED

    def get_value(self, key: str) -> Optional[float]:
        entry = self._cache.get(key)
        if entry and entry.found:
            return entry.value
        return None

    def clear(self):
        with self._global_lock:
            self._cache.clear()
            self._locks.clear()
            self._events.clear()


def merge_path_results(left: Dict[str, PathResult], right: Dict[str, PathResult]) -> Dict[str, PathResult]:
    if left is None:
        left = {}
    if right is None:
        right = {}
    result = dict(left)
    for path_id, path_result in right.items():
        if path_id not in result:
            result[path_id] = path_result
        else:
            existing = result[path_id]
            if path_result.status in [PathStatus.COMPLETED, PathStatus.BLOCKED]:
                result[path_id] = path_result
            elif path_result.node_results:
                merged_nodes = dict(existing.node_results)
                merged_nodes.update(path_result.node_results)
                result[path_id] = PathResult(
                    path_id=path_id,
                    indicator_name=path_result.indicator_name or existing.indicator_name,
                    formula_expr=path_result.formula_expr or existing.formula_expr,
                    formula_index=path_result.formula_index,
                    depth=max(existing.depth, path_result.depth),
                    status=path_result.status,
                    result=path_result.result if path_result.result is not None else existing.result,
                    node_results=merged_nodes,
                    required_vars=path_result.required_vars or existing.required_vars,
                    missing_vars=path_result.missing_vars or existing.missing_vars,
                    child_paths=list(set(existing.child_paths + path_result.child_paths)),
                    error_msg=path_result.error_msg or existing.error_msg
                )
    return result


def merge_var_bindings(left: Dict, right: Dict) -> Dict:
    if left is None:
        left = {}
    if right is None:
        right = {}
    result = dict(left)
    result.update(right)
    return result


def merge_subgoals(left: List, right: List) -> List:
    if right is not None and len(right) > 0:
        return list(right)
    if left is not None:
        return list(left)
    return []


def merge_indicator_tasks(left: List, right: List) -> List:
    if right is not None and len(right) > 0:
        return list(right)
    if left is not None:
        return list(left)
    return []


def take_last(left: Any, right: Any) -> Any:
    if right is not None:
        return right
    return left


def merge_bool_or(left: bool, right: bool) -> bool:
    return (left or False) or (right or False)


class WorkflowState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    context: str
    target_indicator: Annotated[str, take_last]
    formula_context: Annotated[Optional[Dict], take_last]
    oqa_result: Annotated[Optional[Any], take_last]
    current_subgoals: Annotated[List, merge_subgoals]
    evidence_output: Annotated[Optional[Any], take_last]
    all_var_bindings: Annotated[Dict, merge_var_bindings]
    pending_decomposition: Annotated[List[str], take_last]
    pending_tasks: Annotated[List, merge_indicator_tasks]
    decomposition_depth: Annotated[int, take_last]
    max_decomposition_depth: int
    all_path_results: Annotated[Dict[str, PathResult], merge_path_results]
    successful_paths: Annotated[List[str], take_last]
    selected_path_id: Annotated[str, take_last]
    program: Annotated[Optional[Any], take_last]
    execution_result: Annotated[Optional[Any], take_last]
    final_value: Annotated[Optional[float], take_last]
    final_answer: Annotated[str, take_last]
    success: Annotated[bool, merge_bool_or]
    error_msg: Annotated[str, take_last]


class SinglePathState(TypedDict):
    path_id: str
    indicator_name: str
    formula_expr: str
    formula_index: int
    depth: int
    constraints: Dict[str, Any]
    context: str
    required_vars: List[str]
    var_values: Dict[str, float]
    missing_vars: List[str]
    child_results: Dict[str, float]
    result: Optional[float]
    status: str
    error_msg: str


def create_initial_state(query: str, context: str, max_depth: int = 3) -> WorkflowState:
    return {
        "messages": [],
        "query": query,
        "context": context,
        "target_indicator": "",
        "formula_context": None,
        "oqa_result": None,
        "current_subgoals": [],
        "evidence_output": None,
        "all_var_bindings": {},
        "pending_decomposition": [],
        "pending_tasks": [],
        "decomposition_depth": 0,
        "max_decomposition_depth": max_depth,
        "all_path_results": {},
        "successful_paths": [],
        "selected_path_id": "",
        "program": None,
        "execution_result": None,
        "final_value": None,
        "final_answer": "",
        "success": False,
        "error_msg": ""
    }