import pytest
from royalemind.coach import add_match, analyze_notes, connect, history, progress

def test_notes_generate_coaching():
    review=analyze_notes('loss','Overcommitted elixir on defense')
    topics=[x['topic'] for x in review['tips']]
    assert 'Elixir management' in topics
    assert 'Defense' in topics
    assert 'Loss review' in topics

def test_store_video_and_progress(tmp_path):
    with connect(tmp_path/'coach.sqlite3') as db:
        mid=add_match(db,tmp_path/'uploads',outcome='win',notes='spell',
                      video=b'example',filename='../../replay.mp4')
        assert history(db)[0]['id']==mid
        assert (tmp_path/'uploads'/(mid+'.mp4')).read_bytes()==b'example'
        assert progress(db)['win_rate']==100

def test_reject_invalid_values(tmp_path):
    with connect(tmp_path/'db.sqlite3') as db:
        with pytest.raises(ValueError):
            add_match(db,tmp_path,outcome='bad')
        with pytest.raises(ValueError):
            add_match(db,tmp_path,video=b'bad',filename='bad.exe')
        with pytest.raises(ValueError):
            add_match(db,tmp_path,notes='x'*4001)

def test_no_notes_gives_practice():
    assert analyze_notes('unknown','')['tips'][0]['topic']=='Decision review'
