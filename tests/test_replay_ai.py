import json
from unittest.mock import patch
from royalemind.replay_ai import analyze_video

def test_analysis_requires_api_key(tmp_path):
    with patch.dict('os.environ',{'ROYALEMIND_REPLAY_AI_ENABLED':'true'},clear=True):
        try:
            analyze_video(tmp_path/'replay.mp4')
            assert False, 'Expected missing key error'
        except RuntimeError as error:
            assert 'OPENAI_API_KEY' in str(error)

def test_sampled_frame_response_parsing(tmp_path):
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,*args): return b''
    result={'summary':'Review elixir commitments','observations':[],
            'practice_drills':['Defend once then reassess'],'limitations':['Sparse frames']}
    class FakeResponse(Response): pass
    with patch.dict('os.environ',{'ROYALEMIND_REPLAY_AI_ENABLED':'true'},clear=True), patch('royalemind.replay_ai.sample_frames',return_value=[(10.0,'aGVsbG8=')]), patch(
        'royalemind.replay_ai.urlopen',return_value=FakeResponse()), patch(
        'royalemind.replay_ai.json.load',return_value={
        'output':[{'content':[{'type':'output_text','text':json.dumps(result)}]}]}):
        report=analyze_video(tmp_path/'replay.mp4',api_key='test-only')
    assert report['summary']=='Review elixir commitments'
    assert 'sampled video frames' in report['analysis_method']

def test_api_key_alone_never_enables_paid_analysis(tmp_path):
    import pytest
    for flag in ('', 'false', 'TRUE', '1'):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only', 'ROYALEMIND_REPLAY_AI_ENABLED': flag}, clear=True), patch('royalemind.replay_ai.sample_frames') as frames, patch('royalemind.replay_ai.urlopen') as network:
            with pytest.raises(RuntimeError, match='disabled'):
                analyze_video(tmp_path/'replay.mp4', api_key='also-test-only')
            frames.assert_not_called()
            network.assert_not_called()
