from argparse import ArgumentParser
import sys
import os
from utils.log_utils import setup_logger
from agents.workflow import main as workflow_main
import traceback
import json
from tqdm import tqdm
import re
import random
parser = ArgumentParser()
parser.add_argument('--model_name', type=str, default='openai')
parser.add_argument('--max_depth', type=int, default=6)
parser.add_argument('--top_k', type=int, default=3)
parser.add_argument('--example_num', type=int, default=2)
parser.add_argument('--generate_num', type=int, default=5)
parser.add_argument('--dataset_name', type=str, default="FinQA")
parser.add_argument('--question', type=str, default="")
parser.add_argument('--document', type=str, default="")
parser.add_argument('--log_dir', type=str, default="./logs/")
parser.add_argument('--run_id', type=int, default=1)
parser.add_argument('--seed', type=int, default=42)
parser.add_argument('--db_uri', type=str, default='bolt://localhost:7687')
parser.add_argument('--db_user', type=str, default='neo4j')
parser.add_argument('--db_password', type=str, default='')
parser.add_argument('--lang', type=str, default='en', choices=['zh', 'en'],
                    help='Language for question analysis and evidence extraction (zh or en)')
args = parser.parse_args()


def read_file(root_path, query_field, context_field,answer_field, table_field=None):
    data_list = []
    for filename in os.listdir(root_path):
        if filename.endswith('.json'):
            filepath = os.path.join(root_path, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if table_field:
                    for d in data:
                        data_list.append({
                            'query': d[query_field],
                            'context': d[context_field] + '\n' + d[table_field],
                            'answer': d[answer_field]
                        })
                else:
                    for d in data:
                        data_list.append({
                            'query': d[query_field],
                            'context': d[context_field],
                            'answer': d[answer_field]
                        })
    return data_list


def load_dataset(dataset_name):
    data_list = [] 
    if dataset_name == 'CFBenchmark':
        data_list = read_file('data/CFBenchmark','question','context','answer')
        data_list = random.sample(data_list, 50)
    elif dataset_name == 'FinanceReasoning':
        data_list = read_file('data/FinanceReasoning','question','context','ground_truth')
        data_list = random.sample(data_list, 50)
    elif dataset_name == 'FinQA':
        data_list = read_file('data/FinQA','question','context','answer','table')
        data_list = random.sample(data_list, 50)
    elif dataset_name == 'TAT-QA':
        data_list = read_file('data/TAT-QA','question','context','answer','table')
        data_list = random.sample(data_list, 50)
    return data_list

def extract_queries_from_file(file_path: str, encoding: str = "utf-8"):
    """
    Read a txt file and extract all lines starting with 'Query:' into a list.
    """
    with open(file_path, "r", encoding=encoding) as f:
        text = f.read()

    return [q.strip() for q in re.findall(r"(?m)^Query:\s*(.+?)\s*$", text)]

if __name__ == '__main__':
    file_name = f'model_{args.model_name}'
    log_file_path = args.log_dir + args.dataset_name + '/' + file_name + '_valid.log'
    logger = setup_logger(log_file_path)
    data = load_dataset(args.dataset_name)

    try:
        for d in tqdm(data):

            result = workflow_main(d['query'], d['context'], args)

            with open(f'logs/result/{args.dataset_name}_{args.model_name}_valid_res.log', 'a+', encoding='utf-8') as rf:
                rf.write(f'Query: {d["query"]}\n')
                rf.write(f'Context: {d["context"]}\n')
                rf.write(f'Success: {result["success"]}\n')
                rf.write(f'Answer: {result["answer"]}\n')
                rf.write(f'Result: {result["result"]}\n')
                rf.write(f'Ground_truth: {d["answer"]}\n')
                rf.write('=' * 100 + '\n')

    except Exception as e:
        with open('logs/run_log/error_test.log', 'a+', encoding='utf-8') as f:
            f.write(args.dataset_name + '/' + file_name + ' run error\n')
            f.write(traceback.format_exc())
            f.write('\n' + '=' * 100 + '\n\n')

        logger.error(traceback.format_exc())