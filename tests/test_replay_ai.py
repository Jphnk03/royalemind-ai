import json
from unittest.mock import patch
import pytest
from royalemind.replay_ai import analyze_video

def test_analysis_requires_api_key(tmp_path):
    with patch.dict('os.environ',{'ROYALEMIND_REPLAY_AI_ENABLED':'true'},clear=True):
        try:
            analyze_video(tmp_path/'replay.mp4')
            assert False, 'Expected missing key error'
        except RuntimeError as error:
            assert 'OPENAI_API_KEY' in str(error)

def test_disabled_even_with_a_key(tmp_path):
    with patch.dict('os.environ',{},clear=True), patch('royalemind.replay_ai.sample_frames') as sample:
        with pytest.raises(RuntimeError, match='Replay AI is disabled'):
            analyze_video(tmp_path/'replay.mp4',api_key='test-only')
        sample.assert_not_called()

def test_sampled_frame_response_parsing(tmp_path):
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,*args): return b''
    result={'summary':'Review elixir commitments','observations':[],
            'practice_drills':['Defend once then reassess'],'limitations':['Sparse frames']}
    class FakeResponse(Response): pass
    with patch.dict('os.environ',{'ROYALEMIND_REPLAY_AI_ENABLED':'true'}), patch('royalemind.replay_ai.sample_frames',return_value=[(10.0,'aGVsbG8=')]), patch(
        'royalemind.replay_ai.urlopen',return_value=FakeResponse()), patch(
        'royalemind.replay_ai.json.load',return_value={
        'output':[{'content':[{'type':'output_text','text':json.dumps(result)}]}]}):
        report=analyze_video(tmp_path/'replay.mp4',api_key='test-only')
    assert report['summary']=='Review elixir commitments'
    assert 'sampled video frames' in report['analysis_method']
