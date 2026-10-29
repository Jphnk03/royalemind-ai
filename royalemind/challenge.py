"""20-win challenge preparation metrics; no claim of predicting win probability."""
from collections import Counter

def challenge_summary(matches, target=20, loss_limit=3):
    if target < 1 or loss_limit < 1:
        raise ValueError('Invalid challenge settings')
    outcomes = [m['outcome'] for m in matches if m['outcome'] in ('win','loss')]
    wins = sum(x == 'win' for x in outcomes)
    losses = len(outcomes)-wins
    recent = outcomes[:20]
    by_matchup = {}
    for m in matches:
        matchup = (m.get('opponent') or 'Unknown').strip() or 'Unknown'
        if m['outcome'] not in ('win','loss'): continue
        item = by_matchup.setdefault(matchup,{'wins':0,'losses':0})
        item['wins' if m['outcome']=='win' else 'losses'] += 1
    focus = Counter()
    for m in matches:
        review = m.get('review') or {}
        for tip in review.get('tips',[]):
            focus[tip['topic']] += 1
    return {'target_wins':target,'loss_limit':loss_limit,'recorded_wins':wins,
            'recorded_losses':losses,'recent_20_win_rate':round(100*recent.count('win')/len(recent),1) if recent else None,
            'matchups':by_matchup,'top_focus':focus.most_common(5),
            'note':'Practice log totals are not an official challenge run or a prediction of success.'}

def analyze_decision(elixir_self, elixir_opponent, play_cost, context):
    """Basic decision check; cannot infer hidden cards or unseen video frames."""
    for v in (elixir_self, elixir_opponent, play_cost):
        if not isinstance(v,int) or not 0<=v<=10:
            raise ValueError('Elixir and card cost must be integers between 0 and 10')
    if play_cost>elixir_self:
        raise ValueError('Card cost exceeds available elixir')
    if context not in ('attack','defend','cycle','unknown'):
        raise ValueError('Unknown decision context')
    remaining = elixir_self-play_cost
    advice = []
    if context=='attack' and remaining<3:
        advice.append('High commitment: review the opponent counterpush and whether a cheaper attack was possible.')
    if context=='defend':
        advice.append('Check whether this defense traded positively and preserved counterpush troops.')
    if context=='cycle':
        advice.append('Track the opponent\'s counter card before cycling this card.')
    if not advice:
        advice.append('Compare this move with one alternative using the replay timestamp.')
    return {'remaining_elixir':remaining,'known_elixir_difference':elixir_self-elixir_opponent,
            'review_prompts':advice,'confidence':'limited: based only on entered values'}
