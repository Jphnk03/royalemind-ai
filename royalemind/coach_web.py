"""Single-user localhost web server; no external services or automatic video analysis."""
import cgi
import base64
import hmac
import json
import os
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .coach import add_match, connect, history, progress
from .challenge import challenge_summary, analyze_decision
from .replay_ai import analyze_video

STATIC = Path(__file__).resolve().parent.parent/'coach_static'
VIDEO_LIMIT = 100*1024*1024
UPLOAD_LIMIT = 250*1024*1024
LIMIT = UPLOAD_LIMIT + 65536

def prepare_replay(video, filename):
    """Compress oversized recordings to MP4 without retaining uncompressed copies."""
    if len(video) <= VIDEO_LIMIT:
        return video, filename
    suffix = Path(filename.replace('\\\\', '/')).suffix.lower()
    if suffix not in ('.mp4', '.mov', '.webm'):
        raise ValueError('Video must be MP4, MOV or WebM')
    with tempfile.TemporaryDirectory(prefix='royalemind-replay-') as folder:
        source = Path(folder) / ('input' + suffix)
        target = Path(folder) / 'compressed.mp4'
        source.write_bytes(video)
        # 720p, 24fps, H.264. Re-encode more aggressively on large recordings.
        for crf in (30, 35, 39):
            command = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error',
                       '-y', '-i', str(source), '-t', '1800', '-vf',
                       'scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2',
                       '-r', '24', '-an', '-c:v', 'libx264', '-preset', 'veryfast',
                       '-crf', str(crf), '-movflags', '+faststart', str(target)]
            try:
                subprocess.run(command, check=True, timeout=150, capture_output=True)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
                raise ValueError('Video compression failed; try a shorter replay') from exc
            if target.stat().st_size <= VIDEO_LIMIT:
                return target.read_bytes(), 'replay.mp4'
        raise ValueError('Replay is still too large after compression; trim the recording')


def handler(db_path, uploads):
    class Handler(BaseHTTPRequestHandler):
        def authenticate(self):
            secret=os.environ.get('ROYALEMIND_ACCESS_PASSWORD','')
            if not secret:
                if os.environ.get('ROYALEMIND_PUBLIC')=='1':
                    self.send_json(503,{'error':'Private access password not configured'})
                    return False
                return True
            header=self.headers.get('Authorization','')
            expected='Basic '+base64.b64encode(('coach:'+secret).encode()).decode()
            if not hmac.compare_digest(header,expected):
                self.send_response(401)
                self.send_header('WWW-Authenticate','Basic realm="RoyaleMind Private Pilot"')
                self.send_header('Cache-Control','no-store')
                self.send_header('Content-Length','0')
                self.end_headers()
                return False
            return True
        def send_bytes(self, status, body, mime='application/json'):
            self.send_response(status)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('X-Frame-Options','DENY')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self'")
            self.end_headers()
            self.wfile.write(body)
        def send_json(self, status, value):
            self.send_bytes(status,json.dumps(value).encode())
        def do_GET(self):
            if not self.authenticate(): return
            path=urlsplit(self.path).path
            assets={'/':('index.html','text/html; charset=utf-8'),
                    '/style.css':('style.css','text/css; charset=utf-8'),
                    '/app.js':('app.js','application/javascript; charset=utf-8')}
            if path in assets:
                name,mime=assets[path]
                return self.send_bytes(200,(STATIC/name).read_bytes(),mime)
            if path in ('/api/matches','/api/progress','/api/challenge'):
                with connect(db_path) as db:
                    return self.send_json(200,history(db) if path.endswith('matches') else challenge_summary(history(db)) if path.endswith('challenge') else progress(db))
            if path.startswith('/api/video/'):
                mid=path.split('/')[-1]
                with connect(db_path) as db:
                    row=db.execute('SELECT video_file FROM matches WHERE id=?',(mid,)).fetchone()
                if row and row['video_file']:
                    file=Path(uploads)/row['video_file']
                    if file.is_file():
                        mime={'.mp4':'video/mp4','.mov':'video/quicktime','.webm':'video/webm'}[file.suffix]
                        return self.send_bytes(200,file.read_bytes(),mime)
            return self.send_json(404,{'error':'Not found'})
        def do_POST(self):
            if not self.authenticate(): return
            if urlsplit(self.path).path.startswith('/api/analyze/'):
                mid=urlsplit(self.path).path.rsplit('/',1)[-1]
                with connect(db_path) as db:
                    row=db.execute('SELECT video_file FROM matches WHERE id=?',(mid,)).fetchone()
                if not row or not row['video_file']:
                    return self.send_json(404,{'error':'Replay video not found'})
                try:
                    report=analyze_video(Path(uploads)/row['video_file'])
                    return self.send_json(200,report)
                except Exception as exc:
                    self.log_error('Replay analysis failed: %s',type(exc).__name__)
                    return self.send_json(503,{'error':'Replay analysis unavailable. Check API key, ffmpeg and server logs.'})
            if urlsplit(self.path).path=='/api/decision':
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    if not 0<size<=4096: return self.send_json(413,{'error':'Invalid request size'})
                    if self.headers.get_content_type()!='application/json': return self.send_json(415,{'error':'Expected JSON'})
                    data=json.loads(self.rfile.read(size))
                    return self.send_json(200,analyze_decision(data['own'],data['enemy'],data['cost'],data['context']))
                except (ValueError,TypeError,KeyError,AttributeError) as exc:
                    return self.send_json(400,{'error':str(exc)})
            if urlsplit(self.path).path!='/api/matches':
                return self.send_json(404,{'error':'Not found'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=LIMIT:
                    return self.send_json(413,{'error':'Upload exceeds 250 MB limit'})
                if self.headers.get_content_type()!='multipart/form-data':
                    return self.send_json(415,{'error':'Expected multipart upload'})
                form=cgi.FieldStorage(fp=self.rfile,headers=self.headers,
                    environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':self.headers['Content-Type'],
                             'CONTENT_LENGTH':str(size)},keep_blank_values=True)
                def field(name):
                    item=form[name] if name in form else None
                    return item.value if item is not None and not isinstance(item,list) and item.filename is None else ''
                video_field=form['video'] if 'video' in form else None
                video=video_field.file.read(UPLOAD_LIMIT+1) if video_field is not None and video_field.filename else None
                if video is not None:
                    if len(video)>UPLOAD_LIMIT: return self.send_json(413,{'error':'Video exceeds 250 MB limit'})
                    video, upload_name = prepare_replay(video,video_field.filename)
                else:
                    upload_name = ''
                with connect(db_path) as db:
                    mid=add_match(db,uploads,outcome=field('outcome') or 'unknown',
                                  opponent=field('opponent'),deck=field('deck'),notes=field('notes'),
                                  video=video,filename=upload_name)
                return self.send_json(201,{'id':mid})
            except (ValueError,TypeError) as exc:
                return self.send_json(400,{'error':str(exc)})
    return Handler

def main():
    directory=Path(os.environ.get('ROYALEMIND_COACH_DATA','coach_data')).resolve()
    directory.mkdir(parents=True,exist_ok=True)
    db_path=directory/'coach.sqlite3'
    with connect(db_path): pass
    port=int(os.environ.get('PORT','8765'))
    public=os.environ.get('ROYALEMIND_PUBLIC')=='1'
    server=ThreadingHTTPServer(('0.0.0.0' if public else '127.0.0.1',port),handler(db_path,directory/'uploads'))
    print(f'RoyaleMind Coach listening on port {port} (public binding: {public})')
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()

if __name__=='__main__':
    main()
