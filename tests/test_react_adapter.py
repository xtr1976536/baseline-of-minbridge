import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from react_adapter import request_prefix,adapt_response
class AdapterTests(unittest.TestCase):
    def thought(self,raw):return adapt_response('hotpotqa','Examples...\nThought 2:',raw,['\nObservation 2:'])
    def test_exact_duplicate_response_is_one_step(self):
        raw='Thought 2: Check the page.\nAction 2: Search[Alpha]'
        result,info=self.thought(raw+raw)
        self.assertEqual(result,'Check the page.\nAction 2: Search[Alpha]')
        self.assertEqual(info['exact_duplicate_copies_removed'],1)
    def test_different_repeated_steps_still_rejected(self):
        with self.assertRaises(ValueError):self.thought('Thought 2: First.\nAction 2: Search[A]Thought 2: Different.\nAction 2: Search[B]')
    def test_missing_newline_is_display_only(self):
        result,_=self.thought('Thought 2: Check the page.Action 2: Search[Alpha]')
        self.assertEqual(result,'Check the page.\nAction 2: Search[Alpha]')
    def test_generated_observation_discarded(self):
        result,info=self.thought('Check.\nAction 2: Lookup[year]\nObservation 2: fabricated evidence\nThought 3: fake\nAction 3: Finish[wrong]')
        self.assertEqual(result,'Check.\nAction 2: Lookup[year]')
        self.assertTrue(info['discarded_generated_observation'])
        self.assertNotIn('fabricated',result)
    def test_action_only_label_removed(self):
        self.assertEqual(adapt_response('fever','Action 3:','Action 3: Finish[SUPPORTS]',['\n'])[0],'Finish[SUPPORTS]')
    def test_action_only_never_guessed_from_reasoning(self):
        with self.assertRaises(ValueError):adapt_response('fever','Action 3:','I think the answer is SUPPORTS',['\n'])
    def test_wrong_step_never_renumbered(self):
        with self.assertRaises(ValueError):self.thought('Thought 1: Restart.\nAction 1: Finish[yes]')
    def test_multiple_actions_rejected(self):
        with self.assertRaises(ValueError):self.thought('Check.\nAction 2: Search[A]\nAction 3: Finish[yes]')
    def test_author_missing_action_retry_path(self):
        self.assertEqual(self.thought('Only a thought without action.')[0],'Only a thought without action.')
    def test_prefix_original_suffix(self):
        original='author text\nThought 4:';prefix=request_prefix('hotpotqa',original)
        self.assertTrue((prefix+original).endswith(original));self.assertIn('observations come only from the environment',prefix)
    def test_household_action(self):
        self.assertEqual(adapt_response('alfworld','task\n>','Action: go to fridge 1',['\n'])[0],'go to fridge 1')
    def test_household_echoed_prompt_marker(self):
        self.assertEqual(adapt_response('alfworld','task\n>','> go to fridge 1',['\n'])[0],'go to fridge 1')
    def test_household_local_stop(self):
        self.assertEqual(adapt_response('alfworld','task\n>','think: inspect fridge\nObservation: hallucination',['\n'])[0],'think: inspect fridge')
    def test_shop_action(self):
        self.assertEqual(adapt_response('webshop','Action:','Action: search[blue hat]',['\n'])[0],'search[blue hat]')
    def test_shop_unknown_command_rejected(self):
        with self.assertRaises(ValueError):adapt_response('webshop','Action:','buy[hat]',['\n'])


class EnvironmentLogTests(unittest.TestCase):
    def test_observation_and_reward_pass_through_unchanged(self):
        import json,tempfile
        from react_logging import trace_environment
        class Environment:
            def step(self,action):
                if action=='invalid':raise AssertionError('not allowed')
                return ('real observation',.5,False,{'evidence':'real'})
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'environment.jsonl';env=trace_environment(Environment(),path)
            self.assertEqual(env.step('search[test]'),('real observation',.5,False,{'evidence':'real'}))
            with self.assertRaises(AssertionError):env.step('invalid')
            events=[json.loads(l) for l in path.read_text().splitlines()]
            self.assertEqual(events[0]['result'][0],'real observation')
            self.assertEqual(events[1]['error'],'AssertionError: not allowed')

class EpisodeLogTests(unittest.TestCase):
    def test_webshop_score_is_not_changed(self):
        import json,tempfile
        from react_logging import trace_webshop_episodes
        calls=[]
        def original(session,prompt,to_print=True):
            calls.append((session,prompt,to_print));return .25
        namespace={'webshop_run':original}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'episodes.jsonl';trace_webshop_episodes(namespace,path)
            self.assertEqual(namespace['webshop_run']('fixed_3','original prompt',False),.25)
            self.assertEqual(json.loads(path.read_text()),{'session':'fixed_3','reward':.25,'success':False})
        self.assertEqual(calls,[('fixed_3','original prompt',False)])

if __name__=='__main__':unittest.main()
