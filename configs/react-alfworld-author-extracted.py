import os
import openai
import yaml
import alfworld
import alfworld.agents.environment
with open('base_config.yaml') as reader:
    config = yaml.safe_load(reader)
split = 'eval_out_of_distribution'
env = getattr(alfworld.agents.environment, config['env']['type'])(config, train_eval=split)
env = env.init_env(batch_size=1)

def process_ob(ob):
    if ob.startswith('You arrive at loc '):
        ob = ob[ob.find('. ') + 2:]
    return ob
import json
folder = './prompts/'
prompt_file = 'alfworld_3prompts.json'
with open(folder + prompt_file, 'r') as f:
    d = json.load(f)
import sys

def alfworld_run(prompt, to_print=True, ob=''):
    init_prompt = prompt + ob + '\n>'
    prompt = ''
    if to_print:
        print(ob)
        sys.stdout.flush()
    for i in range(1, 50):
        action = llm(init_prompt + prompt, stop=['\n']).strip()
        observation, reward, done, info = env.step([action])
        observation, reward, done = (process_ob(observation[0]), info['won'][0], done[0])
        if action.startswith('think:'):
            observation = 'OK.'
        if to_print:
            print(f'Act {i}: {action}\nObs {i}: {observation}')
            sys.stdout.flush()
        prompt += f' {action}\n{observation}\n>'
        if done:
            return reward
    return 0
prefixes = {'pick_and_place': 'put', 'pick_clean_then_place': 'clean', 'pick_heat_then_place': 'heat', 'pick_cool_then_place': 'cool', 'look_at_obj': 'examine', 'pick_two_obj': 'puttwo'}
cnts = [0] * 6
rs = [0] * 6
