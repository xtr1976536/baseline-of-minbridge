import os
import json

import re
from typing import Union


def read_file(root_path, query_field, context_field,answer_field, table_field=None):
    data_list = []
    for filename in os.listdir(root_path):
        if filename.endswith('_nsdata.json'):
            continue

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
        data_list = read_file('./CFBenchmark','question','context','answer')
    elif dataset_name == 'FinanceReasoning':
        data_list = read_file('./FinanceReasoning','question','context','ground_truth')
    elif dataset_name == 'FinQA':
        data_list = read_file('./FinQA','question','context','answer','table')
    elif dataset_name == 'TAT-QA':
        data_list = read_file('./TAT-QA','question','context','answer','table')   
    return data_list

def is_valid_ground_truth_simple(value: Union[str, None]) -> bool:
    """
    简化优化版，正确处理各种数字格式
    """
    if not isinstance(value, str):
        return False
    
    clean_value = value.strip()
    if not clean_value:
        return False
    
    # 检查是否包含数字
    if not re.search(r'\d', clean_value):
        return False
    
    # 主匹配模式：支持各种数字格式
    # 使用更灵活的数字匹配：(?:\d{1,3}(?:,\d{3})*|\d+)
    # 这匹配：1) 有千位分隔符的数字 2) 无千位分隔符的数字
    main_pattern = r'^\s*[-]?\s*[$¥€£]?\s*(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?\s*[%]?\s*$'
    
    # 首先检查是否匹配主模式
    if not re.match(main_pattern, clean_value):
        return False
    
    # 额外检查：确保不是多个数值
    # 对于有逗号的情况，需要区分是千位分隔符还是多个值的分隔符
    
    # 移除货币符号、百分号和负号，只保留数字、逗号和点号
    temp = re.sub(r'[-$¥€£%\s]', '', clean_value)
    
    if ',' in temp:
        # 分割数字部分
        parts = temp.split(',')
        
        # 情况1：标准千位分隔符（从右向左每3位一个逗号）
        # 检查除了第一部分外，其他部分是否都是3位数字
        all_three_digit = True
        for i in range(1, len(parts)):
            if len(parts[i]) != 3 or not parts[i].isdigit():
                all_three_digit = False
                break
        
        if all_three_digit:
            # 是千位分隔符，有效
            return True
        
        # 情况2：多个数值用逗号分隔
        # 检查是否有类似 "120000000, 50000000" 的模式
        # 即逗号前后都有较长数字（>3位）
        for i in range(len(parts) - 1):
            if len(parts[i]) > 3 and len(parts[i + 1]) > 3:
                # 两个部分都是长数字，很可能是多个值
                return False
        
        # 情况3：混合情况，谨慎处理
        # 如果第一部分长度<=3且后面有3位数字部分，可能是千位分隔符
        if len(parts[0]) <= 3:
            # 检查后面是否都是3位数字
            three_digit_after = True
            for i in range(1, len(parts)):
                if len(parts[i]) != 3:
                    three_digit_after = False
                    break
            
            if three_digit_after:
                return True
    
    return True


if __name__ == "__main__":
    data1 = load_dataset('FinQA')
    data2 = load_dataset('TAT-QA')
    problem_clean = []
    for d in data1:
        if ',' not in d['answer'] and (d['answer'].endswith('million') or d['answer'].endswith('billion')):
            continue
        if not is_valid_ground_truth_simple(d['answer']):
            problem_clean.append(d)
    for d in data2:
        if ',' not in d['answer'] and (d['answer'].endswith('million') or d['answer'].endswith('billion')):
            continue
        if not is_valid_ground_truth_simple(d['answer']):
            problem_clean.append(d)
    # with open('remove_problem.json','r') as f:
    #     data = json.load(f)
    
    # problem_clean = []
    # for d in data:
    #     if ',' not in d['answer'] and (d['answer'].endswith('million') or d['answer'].endswith('billion')):
    #         continue
    #     else:
    #         problem_clean.append(d)
    with open('remove_problem.json','w') as f:
        json.dump(problem_clean,f,indent=4)
    
    # print(problem_clean)