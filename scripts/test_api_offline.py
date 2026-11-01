"""模拟网络响应，不读取密钥、不产生 API 费用。"""
import os, unittest
from unittest.mock import patch,Mock
import requests
from api_compat import generate


class OfflineTransportTests(unittest.TestCase):
    def response(self,data,status=200):
        r=Mock(status_code=status)
        r.json.return_value=data
        r.raise_for_status.side_effect=requests.HTTPError(str(status)) if status>=400 else None
        return r

    def run_with(self,responses):
        return patch('requests.post',side_effect=responses)

    @patch.dict(os.environ,{'OPENAI_API_KEY':'offline-dummy','OPENAI_BASE_URL':'https://api.deepseek.com/v1'})
    @patch('api_compat.time.sleep')
    def test_empty_retry_preserves_request(self,sleep):
        valid={'choices':[{'message':{'content':'Premises: test'}}]}
        with self.run_with([self.response(None),self.response({'choices':None}),self.response(valid)]) as post:
            text,_,_,_=generate('original prompt','gpt-4','deepseek-flash','chat')
        self.assertEqual(text,'Premises: test')
        self.assertEqual(post.call_count,3)
        bodies=[c.kwargs['json'] for c in post.call_args_list]
        self.assertTrue(all(b==bodies[0] for b in bodies))
        self.assertEqual(bodies[0]['stop'],'------')
        self.assertEqual(bodies[0]['max_tokens'],1024)

    @patch.dict(os.environ,{'OPENAI_API_KEY':'offline-dummy','OPENAI_BASE_URL':'https://api.deepseek.com/v1'})
    def test_payment_failure_is_not_retried(self):
        with self.run_with([self.response({},402)]) as post:
            with self.assertRaises(requests.HTTPError):generate('prompt','gpt-4','deepseek-flash','chat')
        self.assertEqual(post.call_count,1)



class ProtocolTransportTests(unittest.TestCase):
    @patch.dict(os.environ,{'OPENAI_API_KEY':'offline-dummy','OPENAI_BASE_URL':'https://example.invalid/v1'})
    def test_reported_usage_over_budget_is_preserved_not_retried(self):
        response=Mock(status_code=200)
        response.json.return_value={'choices':[{'message':{'content':'test'}}],'usage':{'completion_tokens':1025}}
        with patch('requests.post',return_value=response) as post:
            text,record,_,_=generate('prompt','gpt-4','substitute','chat')
        self.assertEqual(post.call_count,1)
        self.assertEqual(text,'test')
        self.assertEqual(record['_minbridge_request']['max_tokens'],1024)
        self.assertEqual(record['_minbridge_audit_warnings'][0]['reported_difference'],1025)

    @patch.dict(os.environ,{'OPENAI_API_KEY':'offline-dummy','OPENAI_BASE_URL':'https://example.invalid/v1'})
    def test_request_record_preserves_author_settings(self):
        response=Mock(status_code=200)
        response.json.return_value={'choices':[{'message':{'content':'test'}}],'usage':{'completion_tokens':4}}
        with patch('requests.post',return_value=response):
            _,record,_,_=generate('unaltered prompt','gpt-4','substitute','chat')
        req=record['_minbridge_request']
        self.assertEqual(req['messages'],[{'role':'user','content':'unaltered prompt'}])
        self.assertEqual(req['max_tokens'],1024)
        self.assertNotIn('Authorization',str(req))


    @patch.dict(os.environ,{'OPENAI_API_KEY':'offline-dummy','OPENAI_BASE_URL':'https://example.invalid/v1'})
    def test_hidden_reasoning_is_not_misclassified_as_visible_overflow(self):
        response=Mock(status_code=200)
        response.json.return_value={'choices':[{'message':{'content':'test'}}],
            'usage':{'completion_tokens':1182,'completion_tokens_details':{'reasoning_tokens':397}}}
        with patch('requests.post',return_value=response):
            text,_,_,_=generate('prompt','gpt-4','substitute','chat')
        self.assertEqual(text,'test')

if __name__=='__main__':unittest.main()
