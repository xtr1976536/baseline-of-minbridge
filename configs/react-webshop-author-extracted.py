import os
import openai
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
WEBSHOP_URL = 'http://3.83.245.205:3000'
ACTION_TO_TEMPLATE = {'Description': 'description_page.html', 'Features': 'features_page.html', 'Reviews': 'review_page.html', 'Attributes': 'attributes_page.html'}

def clean_str(p):
    return p.encode().decode('unicode-escape').encode('latin1').decode('utf-8')

def tag_visible(element):
    ignore = {'style', 'script', 'head', 'title', 'meta', '[document]'}
    return element.parent.name not in ignore and (not isinstance(element, Comment))

def webshop_text(session, page_type, query_string='', page_num=1, asin='', options={}, subpage='', **kwargs):
    if page_type == 'init':
        url = f'{WEBSHOP_URL}/{session}'
    if page_type == 'search':
        url = f'{WEBSHOP_URL}/search_results/{session}/{query_string}/{page_num}'
    elif page_type == 'item':
        url = f'{WEBSHOP_URL}/item_page/{session}/{asin}/{query_string}/{page_num}/{options}'
    elif page_type == 'item_sub':
        url = f'{WEBSHOP_URL}/item_sub_page/{session}/{asin}/{query_string}/{page_num}/{subpage}/{options}'
    elif page_type == 'end':
        url = f'{WEBSHOP_URL}/done/{session}/{asin}/{options}'
    html = requests.get(url).text
    html_obj = BeautifulSoup(html, 'html.parser')
    texts = html_obj.findAll(text=True)
    visible_texts = list(filter(tag_visible, texts))
    if False:
        return ' [SEP] '.join((t.strip() for t in visible_texts if t != '\n'))
    else:
        observation = ''
        option_type = ''
        options = {}
        asins = []
        cnt = 0
        prod_cnt = 0
        just_prod = 0
        for t in visible_texts:
            if t == '\n':
                continue
            if t.replace('\n', '').replace('\\n', '').replace(' ', '') == '':
                continue
            if t.parent.name == 'button':
                processed_t = f'\n[{t}] '
            elif t.parent.name == 'label':
                if f"'{t}'" in url:
                    processed_t = f'[[{t}]]'
                else:
                    processed_t = f'[{t}]'
                options[str(t)] = option_type
            elif t.parent.get('class') == ['product-link']:
                processed_t = f'\n[{t}] '
                if prod_cnt >= 3:
                    processed_t = ''
                prod_cnt += 1
                asins.append(str(t))
                just_prod = 0
            else:
                processed_t = '\n' + str(t) + ' '
                if cnt < 2 and page_type != 'init':
                    processed_t = ''
                if just_prod <= 2 and prod_cnt >= 4:
                    processed_t = ''
                option_type = str(t)
                cnt += 1
            just_prod += 1
            observation += processed_t
        info = {}
        if options:
            info['option_types'] = options
        if asins:
            info['asins'] = asins
        if 'Your score (min 0.0, max 1.0)' in visible_texts:
            idx = visible_texts.index('Your score (min 0.0, max 1.0)')
            info['reward'] = float(visible_texts[idx + 1])
            observation = 'Your score (min 0.0, max 1.0): ' + visible_texts[idx + 1]
        return (clean_str(observation), info)

class webshopEnv:

    def __init__(self):
        self.sessions = {}

    def step(self, session, action):
        done = False
        observation_ = None
        if action == 'reset':
            self.sessions[session] = {'session': session, 'page_type': 'init'}
        elif action.startswith('think['):
            observation = 'OK.'
        elif action.startswith('search['):
            assert self.sessions[session]['page_type'] == 'init'
            query = action[7:-1]
            self.sessions[session] = {'session': session, 'page_type': 'search', 'query_string': query, 'page_num': 1}
        elif action.startswith('click['):
            button = action[6:-1]
            if button == 'Buy Now':
                assert self.sessions[session]['page_type'] == 'item'
                self.sessions[session]['page_type'] = 'end'
                done = True
            elif button == 'Back to Search':
                assert self.sessions[session]['page_type'] in ['search', 'item_sub', 'item']
                self.sessions[session] = {'session': session, 'page_type': 'init'}
            elif button == 'Next >':
                assert False
                assert self.sessions[session]['page_type'] == 'search'
                self.sessions[session]['page_num'] += 1
            elif button == '< Prev':
                assert self.sessions[session]['page_type'] in ['search', 'item_sub', 'item']
                if self.sessions[session]['page_type'] == 'search':
                    assert False
                    self.sessions[session]['page_num'] -= 1
                elif self.sessions[session]['page_type'] == 'item_sub':
                    self.sessions[session]['page_type'] = 'item'
                elif self.sessions[session]['page_type'] == 'item':
                    self.sessions[session]['page_type'] = 'search'
                    self.sessions[session]['options'] = {}
            elif button in ACTION_TO_TEMPLATE:
                assert self.sessions[session]['page_type'] == 'item'
                self.sessions[session]['page_type'] = 'item_sub'
                self.sessions[session]['subpage'] = button
            elif self.sessions[session]['page_type'] == 'search':
                assert button in self.sessions[session].get('asins', [])
                self.sessions[session]['page_type'] = 'item'
                self.sessions[session]['asin'] = button
            elif self.sessions[session]['page_type'] == 'item':
                assert 'option_types' in self.sessions[session]
                assert button in self.sessions[session]['option_types'], (button, self.sessions[session]['option_types'])
                option_type = self.sessions[session]['option_types'][button]
                if not 'options' in self.sessions[session]:
                    self.sessions[session]['options'] = {}
                self.sessions[session]['options'][option_type] = button
                observation_ = f'You have clicked {button}.'
        else:
            assert False
        observation, info = webshop_text(**self.sessions[session])
        if observation_:
            observation = observation_
        self.sessions[session].update(info)
        reward = info.get('reward', 0.0)
        return (observation, reward, done)
env = webshopEnv()
prompt1 = "Webshop \nInstruction:  \ni would like a 3 ounce bottle of bright citrus deodorant for sensitive skin, and price lower than 50.00 dollars \n[Search]  \n\nAction: search[3 ounce bright citrus deodorant sensitive skin]\nObservation: \n[Back to Search] \nPage 1 (Total results: 50) \n[Next >] \n[B078GWRC1J] \nBright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce \n$10.99 \n[B078GTKVXY] \nGinger Fresh Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce \n$10.99 \n[B08KBVJ4XN] \nBarrel and Oak - Aluminum-Free Deodorant, Deodorant for Men, Essential Oil-Based Scent, 24-Hour Odor Protection, Cedar & Patchouli Blend, Gentle on Sensitive Skin (Mountain Sage, 2.7 oz, 2-Pack) \n$15.95  \n\nAction: think[B078GWRC1J and B078GTKVXY are bright citrus deodorant less then 50 dollars. I can check B078GWRC1J first.]\nObservation: OK.\n\nAction: click[B078GWRC1J]\nObservation: \n[Back to Search] \n[< Prev] \nscent [assorted scents][bright citrus][calming lavender][ginger fresh][simply non-scents]\nsize [travel set (4-pack)][3 ounce (pack of 1)][3-ounce (2-pack)]\nBright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce \nPrice: $10.99 \nRating: N.A. \n[Description] \n[Features] \n[Reviews] \n[Buy Now]  \n\nAction: think[For 3 ounce bottle of bright citrus deodorant for sensitive skin, the item has options 'bright citrus' and '3 ounce (pack of 1)' and seems good to buy.]\nObservation: OK.\n\nAction: click[bright citrus]\nObservation: You have clicked bright citrus. \n\nAction: click[3 ounce (pack of 1)]\nObservation: You have clicked 3 ounce (pack of 1). \n\nAction: click[Buy Now]\n"
prompt1_actonly = 'Webshop \nInstruction:  \ni would like a 3 ounce bottle of bright citrus deodorant for sensitive skin, and price lower than 50.00 dollars \n[Search]  \n\nAction: search[3 ounce bright citrus deodorant sensitive skin]\nObservation: \n[Back to Search] \nPage 1 (Total results: 50) \n[Next >] \n[B078GWRC1J] \nBright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce \n$10.99 \n[B078GTKVXY] \nGinger Fresh Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce \n$10.99 \n[B08KBVJ4XN] \nBarrel and Oak - Aluminum-Free Deodorant, Deodorant for Men, Essential Oil-Based Scent, 24-Hour Odor Protection, Cedar & Patchouli Blend, Gentle on Sensitive Skin (Mountain Sage, 2.7 oz, 2-Pack) \n$15.95  \n\nAction: click[B078GWRC1J]\nObservation: \n[Back to Search] \n[< Prev] \nscent [assorted scents][bright citrus][calming lavender][ginger fresh][simply non-scents]\nsize [travel set (4-pack)][3 ounce (pack of 1)][3-ounce (2-pack)]\nBright Citrus Deodorant by Earth Mama | Natural and Safe for Sensitive Skin, Pregnancy and Breastfeeding, Contains Organic Calendula 3-Ounce \nPrice: $10.99 \nRating: N.A. \n[Description] \n[Features] \n[Reviews] \n[Buy Now]  \n\nAction: click[bright citrus]\nObservation: You have clicked bright citrus. \n\nAction: click[3 ounce (pack of 1)]\nObservation: You have clicked 3 ounce (pack of 1). \n\nAction: click[Buy Now]\n'

def webshop_run(idx, prompt, to_print=True):
    action = 'reset'
    init_prompt = prompt
    prompt = ''
    for i in range(15):
        try:
            res = env.step(idx, action)
            observation = res[0]
        except AssertionError:
            observation = 'Invalid action!'
        if action.startswith('think'):
            observation = 'OK.'
        if to_print:
            print(f'Action: {action}\nObservation: {observation}\n')
            sys.stdout.flush()
        if i:
            prompt += f' {action}\nObservation: {observation}\n\nAction:'
        else:
            prompt += f'{observation}\n\nAction:'
        if res[2]:
            return res[1]
        action = llm(init_prompt + prompt[-(6400 - len(init_prompt)):], stop=['\n']).lstrip(' ')
    return 0

def run_episodes(prompt, n=50):
    rs = []
    cnt = 0
    for i in range(n):
        print('-----------------')
        print(i)
        try:
            r = webshop_run(f'fixed_{i}', prompt, to_print=True)
        except AssertionError:
            r = 0
            cnt += 1
        rs.append(r)
        if (i + 1) % 1 == 0:
            r, sr, fr = (sum(rs) / len(rs), len([_ for _ in rs if _ == 1]) / len(rs), cnt / len(rs))
            print(i + 1, r, sr, fr)
            print('-------------')
    r, sr, fr = (sum(rs) / len(rs), len([_ for _ in rs if _ == 1]) / n, cnt / n)
    print(r, sr, fr)
    return rs
