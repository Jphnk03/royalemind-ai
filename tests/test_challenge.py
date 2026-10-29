import pytest
from royalemind.challenge import analyze_decision, challenge_summary

def test_challenge_summary():
    matches=[{'outcome':'win','opponent':'Hog','review':{'tips':[{'topic':'Defense'}]}},
             {'outcome':'loss','opponent':'Hog','review':{'tips':[{'topic':'Elixir'}]}},
             {'outcome':'unknown','opponent':'Other','review':{'tips':[]}}]
    report=challenge_summary(matches)
    assert report['recent_20_win_rate']==50
    assert report['matchups']['Hog']=={'wins':1,'losses':1}
    assert report['top_focus'][0][1]==1

def test_decision_feedback():
    feedback=analyze_decision(7,5,5,'attack')
    assert feedback['remaining_elixir']==2
    assert 'High commitment' in feedback['review_prompts'][0]

@pytest.mark.parametrize('values',[(2,5,4,'attack'),(11,5,2,'attack'),(4,5,2,'bad')])
def test_invalid_decision(values):
    with pytest.raises(ValueError):
        analyze_decision(*values)

def test_invalid_target():
    with pytest.raises(ValueError):
        challenge_summary([],target=0)
