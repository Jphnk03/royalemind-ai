"""Local coaching journal. Replay files are stored, NOT automatically analyzed."""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS matches (
      id TEXT PRIMARY KEY, created_at TEXT, outcome TEXT, opponent TEXT,
      deck TEXT, notes TEXT, video_file TEXT, review TEXT)""")
    db.commit()
    return db

def analyze_notes(outcome, notes):
    """Transparent coaching prompts from written notes, not video inference."""
    lower = notes.lower()
    rules = [
        (('elixir','overcommit','overspend'), 'Elixir management',
         'Pause before your biggest commitment. Count available elixir and plan for a counterpush.'),
        (('cycle','rotation'), 'Card cycle',
         'Track the opponent\'s key defensive card and whether it is back in cycle.'),
        (('defend','defense','counterpush'), 'Defense',
         'Compare the elixir cost of the incoming push and your defense.'),
        (('spell','fireball','log','poison'), 'Spell value',
         'Check whether your spell earned positive elixir value or crucial tower damage.'),
        (('placement','tile','position'), 'Placement',
         'Rewatch the placement and practice a more precise tile.'),
        (('timing','late','early'), 'Timing',
         'Pause before the play and practice the deployment timing.')
    ]
    tips = [{'topic': label, 'exercise': exercise} for words,label,exercise in rules
            if any(word in lower for word in words)]
    if not tips:
        tips = [{'topic': 'Decision review', 'exercise':
                 'Pick a timestamp and record both players\' elixir, your hand, and two possible moves.'}]
    if outcome == 'loss':
        tips.append({'topic': 'Loss review', 'exercise':
                     'Find the first avoidable disadvantage, rather than only the final tower loss.'})
    return {'method': 'Written-note keyword rules; video not analyzed automatically',
            'tips': tips[:6]}

def add_match(db, directory, outcome='unknown', opponent='', deck='', notes='', video=None, filename=''):
    if outcome not in ('win','loss','draw','unknown'):
        raise ValueError('Invalid match result')
    if len(opponent)>120 or len(deck)>500 or len(notes)>4000:
        raise ValueError('Text field too long')
    if video is not None:
        suffix = Path(filename.replace('\\','/')).suffix.lower()
        if suffix not in ('.mp4','.mov','.webm'):
            raise ValueError('Video must be MP4, MOV or WebM')
        if not 0 < len(video) <= 100*1024*1024:
            raise ValueError('Video must be between 1 byte and 100 MB')
    mid = uuid.uuid4().hex
    stored = None
    if video is not None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        stored = mid+suffix
        (directory/stored).write_bytes(video)
        (directory/stored).chmod(0o600)
    try:
        db.execute('INSERT INTO matches VALUES (?,?,?,?,?,?,?,?)',
                   (mid,datetime.now(timezone.utc).isoformat(),outcome,opponent.strip(),
                    deck.strip(),notes.strip(),stored,json.dumps(analyze_notes(outcome,notes))))
        db.commit()
    except Exception:
        if stored: (directory/stored).unlink(missing_ok=True)
        raise
    return mid

def history(db):
    return [{**dict(r), 'review':json.loads(r['review'])} for r in
            db.execute('SELECT * FROM matches ORDER BY created_at DESC')]

def progress(db):
    rows = history(db)
    played = [r for r in rows if r['outcome'] in ('win','loss','draw')]
    wins = sum(r['outcome']=='win' for r in played)
    topics = {}
    for r in rows:
        for tip in r['review']['tips']:
            topics[tip['topic']] = topics.get(tip['topic'],0)+1
    return {'matches':len(rows),'wins':wins,
            'win_rate':round(100*wins/len(played),1) if played else None,
            'focus_areas':topics}
