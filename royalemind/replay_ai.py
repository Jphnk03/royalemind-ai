"""Opt-in video replay analysis using sampled frames and OpenAI Responses API.

Requires ffmpeg on PATH and OPENAI_API_KEY in the server environment.
Frames are transmitted to OpenAI only after the user explicitly requests analysis.
"""
import base64
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

MODEL = os.environ.get('ROYALEMIND_VISION_MODEL', 'gpt-4.1-mini')
PROMPT = """You are RoyaleMind Coach, a careful Clash Royale replay reviewer.
The images are chronological, sparse screenshots of ONE replay. Times are seconds
from the uploaded VIDEO, not necessarily game clock time. The player being coached
may be at the bottom of the game screen; if uncertain, say so. Do not invent
card plays, elixir counts, exact placements, outcomes, or frame details.
Return ONLY a JSON object with fields:
summary (string), observations (array of objects with timestamp_seconds (number),
observation (string), coaching (string), confidence ('high'|'medium'|'low')),
practice_drills (array of strings), limitations (array of strings).
Keep observations <= 6, drills <= 4. If frames do not support concrete
mistakes, describe questions to investigate rather than asserting mistakes.
Focus on elixir discipline, defensive overcommitment, and counterpush timing.
"""
def sample_frames(video_path, count=8):
    if shutil.which('ffmpeg') is None or shutil.which('ffprobe') is None:
        raise RuntimeError('ffmpeg and ffprobe must be installed on the server')
    probe = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                            '-of','default=noprint_wrappers=1:nokey=1',str(video_path)],
                           capture_output=True,text=True,timeout=15,check=True)
    duration = float(probe.stdout.strip())
    if not 0 < duration <= 1800:
        raise ValueError('Replay duration must be between 0 and 30 minutes')
    result = []
    with tempfile.TemporaryDirectory() as temp:
        for i in range(count):
            sec = round(duration * (i+0.5)/count, 1)
            frame = Path(temp)/f'{i}.jpg'
            subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error',
                            '-ss',str(sec),'-i',str(video_path),'-frames:v','1',
                            '-vf','scale=480:-2','-q:v','5','-y',str(frame)],
                           check=True,timeout=20)
            if frame.exists() and frame.stat().st_size:
                result.append((sec,base64.b64encode(frame.read_bytes()).decode('ascii')))
    if not result:
        raise RuntimeError('No replay frames could be extracted')
    return result

def analyze_video(video_path, api_key=None, model=None):
    api_key = api_key or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY is not configured')
    frames = sample_frames(video_path)
    content = [{'type':'input_text','text':PROMPT+' Frame timestamps: '+
                ', '.join(str(t) for t,_ in frames)}]
    for seconds, encoded in frames:
        content.append({'type':'input_text','text':f'Video timestamp: {seconds} seconds'})
        content.append({'type':'input_image','image_url':'data:image/jpeg;base64,'+encoded})
    payload = json.dumps({'model':model or MODEL,'input':[{'role':'user','content':content}],
                          'text':{'format':{'type':'json_object'}},'max_output_tokens':1600}).encode()
    req = Request('https://api.openai.com/v1/responses',data=payload,
                  headers={'Authorization':'Bearer '+api_key,'Content-Type':'application/json'},
                  method='POST')
    with urlopen(req,timeout=100) as response:
        raw = json.load(response)
    texts = [part.get('text','') for item in raw.get('output',[])
             for part in item.get('content',[]) if part.get('type')=='output_text']
    if not texts:
        raise RuntimeError('The vision model returned no analysis')
    result = json.loads(''.join(texts))
    if not isinstance(result,dict) or not isinstance(result.get('observations'),list):
        raise RuntimeError('The vision model returned an unexpected report')
    result['analysis_method'] = 'AI analysis of '+str(len(frames))+' sampled video frames; not continuous gameplay tracking'
    result['model'] = model or MODEL
    return result
