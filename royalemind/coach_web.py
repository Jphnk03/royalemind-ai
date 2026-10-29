"""Single-user localhost web server; no external services or automatic video analysis."""
import cgi
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .coach import add_match, connect, history, progress

STATIC = Path(__file__).resolve().parent.parent/'coach_static'
LIMIT = 100*1024*1024 + 65536

def handler(db_path, uploads):
    class Handler(BaseHTTPRequestHandler):
        def send_bytes(self, status, body, mime='application/json'):
            self.send_response(status)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self'")
            self.end_headers()
            self.wfile.write(body)
        def send_json(self, status, value):
            self.send_bytes(status,json.dumps(value).encode())
        def do_GET(self):
            path=urlsplit(self.path).path
            assets={'/':('index.html','text/html; charset=utf-8'),
                    '/style.css':('style.css','text/css; charset=utf-8'),
                    '/app.js':('app.js','application/javascript; charset=utf-8')}
            if path in assets:
                name,mime=assets[path]
                return self.send_bytes(200,(STATIC/name).read_bytes(),mime)
            if path in ('/api/matches','/api/progress'):
                with connect(db_path) as db:
                    return self.send_json(200,history(db) if path.endswith('matches') else progress(db))
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
            if urlsplit(self.path).path!='/api/matches':
                return self.send_json(404,{'error':'Not found'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=LIMIT:
                    return self.send_json(413,{'error':'Upload exceeds 100 MB limit'})
                if self.headers.get_content_type()!='multipart/form-data':
                    return self.send_json(415,{'error':'Expected multipart upload'})
                form=cgi.FieldStorage(fp=self.rfile,headers=self.headers,
                    environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':self.headers['Content-Type'],
                             'CONTENT_LENGTH':str(size)},keep_blank_values=True)
                def field(name):
                    item=form[name] if name in form else None
                    return item.value if item is not None and not isinstance(item,list) and item.filename is None else ''
                video_field=form['video'] if 'video' in form else None
                video=video_field.file.read(100*1024*1024+1) if video_field is not None and video_field.filename else None
                with connect(db_path) as db:
                    mid=add_match(db,uploads,outcome=field('outcome') or 'unknown',
                                  opponent=field('opponent'),deck=field('deck'),notes=field('notes'),
                                  video=video,filename=video_field.filename if video is not None else '')
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
    server=ThreadingHTTPServer(('127.0.0.1',port),handler(db_path,directory/'uploads'))
    print(f'RoyaleMind Coach at http://127.0.0.1:{port} (local only)')
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()

if __name__=='__main__':
    main()
