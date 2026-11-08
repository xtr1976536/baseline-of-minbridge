import logging
import sys
import os
from argparse import ArgumentParser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.log_utils import setup_logger
from langgraph.graph import END, StateGraph, START

from agents.states import WorkflowState, ThreeStateCache, create_initial_state
from agents.nodes import NodeFactory
from agents.edges import (
    after_question_analysis,
    after_evidence_seeking,
    after_multipath_decomposition,
    after_multipath_compute,
    after_execution,
    after_path_evaluation
)

logger = logging.getLogger("EBFR")

_global_cache = None


def get_global_cache() -> ThreeStateCache:
    global _global_cache
    if _global_cache is None:
        _global_cache = ThreeStateCache()
    return _global_cache


def reset_global_cache():
    global _global_cache
    _global_cache = ThreeStateCache()


def create_operators(config: dict):
    from operators.QuestionAnalyzer import QuestionAnalyzerOperator
    from operators.EvidenceSeeking import EvidenceSeekingOperator
    from operators.ProblemDecomposition import ProblemDecompositionOperator, FinanceKnowledgeGraph
    from operators.Execution import PoTGenerationOperator, PoTExecutor

    model_name = config.get('model_name', 'openai')
    lang = config.get('lang', 'en')

    kg_config = config.get('kg_config', {})
    kg = None
    try:
        kg = FinanceKnowledgeGraph(
            uri=kg_config.get('uri', 'bolt://localhost:7687'),
            user=kg_config.get('user', 'neo4j'),
            password=kg_config.get('password', ''),
            lang=lang
        )
        kg.test_connection()
    except Exception as e:
        logger.warning(f"Failed to connect to knowledge graph: {e}")
        kg = None

    analyzer = QuestionAnalyzerOperator({'model_name': model_name})
    seeker = EvidenceSeekingOperator({'model_name': model_name})
    decomposer = ProblemDecompositionOperator(kg, lang=lang) if kg else None
    generator = PoTGenerationOperator({'model_name': model_name})
    executor = PoTExecutor(lang=lang)

    return {
        'analyzer': analyzer,
        'seeker': seeker,
        'decomposer': decomposer,
        'generator': generator,
        'executor': executor,
        'kg': kg
    }


def create_graph(config: dict = None):
    if config is None:
        config = {'model_name': 'openai', 'lang': 'en'}

    reset_global_cache()
    operators = create_operators(config)

    node_factory = NodeFactory(
        question_analyzer=operators['analyzer'],
        evidence_seeker=operators['seeker'],
        decomposer=operators['decomposer'],
        pot_generator=operators['generator'],
        pot_executor=operators['executor'],
        kg=operators['kg'],
        lang=config.get('lang', 'en')
    )
    node_factory.evidence_cache = get_global_cache()

    workflow = StateGraph(WorkflowState)

    workflow.add_node("question_analysis", node_factory.question_analysis_node)
    workflow.add_node("evidence_seeking", node_factory.evidence_seeking_node)
    workflow.add_node("multipath_decomposition", node_factory.multipath_decomposition_node)
    workflow.add_node("multipath_compute", node_factory.multipath_compute_node)
    workflow.add_node("execution", node_factory.execution_node)
    workflow.add_node("path_evaluation", node_factory.path_evaluation_node)
    workflow.add_node("answer", node_factory.answer_generation_node)
    workflow.add_node("error", node_factory.error_node)
    workflow.add_node("final", node_factory.final_node)

    workflow.add_edge(START, "question_analysis")

    workflow.add_conditional_edges("question_analysis", after_question_analysis, {
        "evidence_seeking": "evidence_seeking",
        "error": "error"
    })

    workflow.add_conditional_edges("evidence_seeking", after_evidence_seeking, {
        "execution": "execution",
        "multipath_compute": "multipath_compute",
        "multipath_decomposition": "multipath_decomposition",
        "error": "error"
    })

    workflow.add_conditional_edges("multipath_decomposition", after_multipath_decomposition, {
        "evidence_seeking": "evidence_seeking",
        "execution": "execution",
        "error": "error"
    })

    workflow.add_conditional_edges("multipath_compute", after_multipath_compute, {
        "answer": "answer",
        "path_evaluation": "path_evaluation",
        "error": "error"
    })

    workflow.add_conditional_edges("execution", after_execution, {
        "answer": "answer",
        "path_evaluation": "path_evaluation",
        "error": "error"
    })

    workflow.add_conditional_edges("path_evaluation", after_path_evaluation, {
        "answer": "answer",
        "error": "error"
    })

    workflow.add_edge("answer", "final")
    workflow.add_edge("error", "final")
    workflow.add_edge("final", END)

    return workflow.compile()


def run_workflow(query: str = None, context: str = None, config: dict = None,
                 model_name: str = None, lang: str = None, max_depth: int = None,
                 db_uri: str = None, db_user: str = None, db_password: str = None,
                 question: str = None, document: str = None, **kwargs):
    if query is None:
        query = question or kwargs.get('question', '')
    if context is None:
        context = document or kwargs.get('document', '')

    if config is None:
        config = {}

    if model_name is not None:
        config['model_name'] = model_name
    elif 'model_name' not in config:
        config['model_name'] = kwargs.get('model_name', 'openai')

    if lang is not None:
        config['lang'] = lang
    elif 'lang' not in config:
        config['lang'] = kwargs.get('lang', 'en')

    if max_depth is not None:
        config['max_depth'] = max_depth
    elif 'max_depth' not in config:
        config['max_depth'] = kwargs.get('max_depth', 3)

    if 'kg_config' not in config:
        config['kg_config'] = {
            'uri': db_uri or kwargs.get('db_uri', 'bolt://localhost:7687'),
            'user': db_user or kwargs.get('db_user', 'neo4j'),
            'password': db_password or kwargs.get('db_password', '')
        }

    graph = create_graph(config)

    inputs = create_initial_state(query, context, config.get('max_depth', 3))

    try:
        final_state = graph.invoke(inputs)
        return {
            "success": final_state.get("success", False),
            "answer": final_state.get("final_answer", ""),
            "value": final_state.get("final_value"),
            "result": final_state.get("final_value"),
            "all_path_results": final_state.get("all_path_results", {}),
            "selected_path_id": final_state.get("selected_path_id", ""),
            "successful_paths": final_state.get("successful_paths", [])
        }
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "answer": f"Execution failed: {e}",
            "value": None,
            "result": None
        }


def main(query, context, args):
    # import yaml

    # with open("llm_config.yaml", "r") as f:
    #     cfg = yaml.safe_load(f)

    config = {
        "model_name": args.model_name,
        "lang": getattr(args, "lang", "en"),
        "max_depth": getattr(args, "max_depth", 3),
        "kg_config": {
            "uri": getattr(args, "db_uri", "bolt://localhost:7687"),
            "user": getattr(args, "db_user", "neo4j"),
            "password": getattr(args, "db_password", "dasi")
        }
    }

    # query = getattr(args, "question", "")
    # context = getattr(args, "document", "")

    result = run_workflow(query, context, config)

    return result

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--model_name', type=str, default='openai')
    parser.add_argument('--max_depth', type=int, default=6)
    parser.add_argument('--top_k', type=int, default=3)
    parser.add_argument('--example_num', type=int, default=2)
    parser.add_argument('--generate_num', type=int, default=5)
    parser.add_argument('--dataset_name', type=str, default="adult")
    parser.add_argument('--question', type=str, default="")
    parser.add_argument('--document', type=str, default="")
    parser.add_argument('--log_dir', type=str, default="./logs/")
    parser.add_argument('--run_id', type=int, default=1)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--db_uri', type=str, default='bolt://localhost:7687')
    parser.add_argument('--db_user', type=str, default='neo4j')
    parser.add_argument('--db_password', type=str, default='dasi')
    parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'],
                        help='Language for question analysis and evidence extraction (zh or en)')
    args = parser.parse_args()
    log_file_path = args.log_dir + '/test.log'
    args.model_name = 'openai'
    logger = setup_logger(log_file_path)
    query = "What should Toft report as earnings per share for the year? Answer to the nearest cent."
    context= '''Toft Co. had 120000 shares of common stock outstanding at January 1. On April 1 it issued 40000 additional shares of common stock. Outstanding all year were 10000 shares of nonconvertible preferred stock on which a dividend of $5 per share was declared during the year. Net income for the year was $480000. 
    '''
    result= main(query, context,args)
    print(result)