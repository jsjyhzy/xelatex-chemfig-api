from binascii import crc32

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel
from sqlalchemy import (BIGINT, BLOB, BOOLEAN, INTEGER, TEXT, TIMESTAMP,
                        Column, create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import func
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

try:
    from .utils import Template, wrap, unwrap, compiling, b2c, bcompress, bdecompress
except ImportError:
    from utils import Template, wrap, unwrap, compiling, b2c, bcompress, bdecompress


template = Template()

engine = create_engine(template.database_uri,
                       connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Cache(Base):
    __tablename__ = 'cache'
    id = Column(INTEGER, primary_key=True)
    request_hash = Column(BIGINT, index=True)
    request = Column(TEXT)
    stdout = Column(BLOB)
    stderr = Column(BLOB)
    attachment = Column(BLOB)
    ctime = Column(TIMESTAMP, server_default=func.now())
    hit = Column(INTEGER, default=0)
    standby = Column(BOOLEAN, default=False)
    failed = Column(BOOLEAN, default=False)

    @property
    def blob(self):
        return bdecompress(self.stdout), bdecompress(self.stderr), bdecompress(self.attachment)

    @blob.setter
    def blob(self, val):
        o, e, a = val
        self.stdout = bcompress(o)
        self.stderr = bcompress(e)
        self.attachment = bcompress(a)

    @property
    def json(self):
        o, e, a = self.blob
        return {
            "failed": self.failed,
            "stdout": b2c(o),
            "stderr": b2c(e),
            "attachment": b2c(a),
            "type": template.content_type_jsons(self.request)
        }


class RenderRequest(BaseModel):
    doc_class: str = wrap(template.default_documentclass)
    doc_option: str = wrap(template.default_documentoption)
    preamble: str = wrap(template.default_preamble)
    content: str = wrap(template.example_latex_code)
    engine: str = template.default_engine
    compilepass: int = 3
    target: str = 'svg'

    @property
    def crc32(self):
        return crc32(bytes(self.to_string(), encoding='utf8'))


Base.metadata.create_all(bind=engine)


# Utility
def get_cache(db_session: Session, req: RenderRequest):
    query = db_session.query(Cache)
    query = query.filter(Cache.request_hash == req.crc32)
    query = query.filter(Cache.request == req.json())
    try:
        return query.first()
    except:
        return None


def get_cache_byid(db_session: Session, cache_id: int):
    query = db_session.query(Cache)
    query = query.filter(Cache.id == cache_id)
    try:
        ret = query.first()
        ret.hit = ret.hit+1
        db_session.merge(ret)
        db_session.commit()
        return query.first()
    except:
        return None


# Dependency
def get_db(request: Request):
    return request.state.db


app = FastAPI()
app.add_middleware(GZipMiddleware)


@app.get('/', content_type=Response(media_type='text/html'))
async def index():
    return await assets('index.html')


@app.post('/')
async def render(req: RenderRequest, db: Session = Depends(get_db)):
    if template.exceed_max_compilepass(req.compilepass):
        return JSONResponse(status_code=400, content={"msg": "Too many compile pass"})
    cache = get_cache(db, req)
    if cache is None:
        db.add(Cache(request_hash=req.crc32, request=req.json()))
        db.commit()
        cache = get_cache(db, req)
    return Response(status_code=302, headers={'Location': f'/by-id/{cache.id}'})


@app.get('/by-id/{cache_id}')
async def getresult(cache_id, db: Session = Depends(get_db)):
    cache = get_cache_byid(db, cache_id)
    if cache is None:
        return Response(status_code=404)
    if cache.standby or cache.failed is True:
        return JSONResponse(content=cache.json)

    context = template.render_jsons(cache.request)
    exec_seq = template.assign_jsons(cache.id, cache.request)
    stdout, stderr, attachment = compiling(exec_seq, context, cache.id)

    cache.blob = (stdout, stderr, attachment)
    if attachment is None:
        cache.failed = True
    else:
        cache.standby = True
    db.merge(cache)
    db.commit()
    cache = get_cache_byid(db, cache_id)
    return JSONResponse(content=cache.json)


@app.get('/purge')
async def purge(db: Session = Depends(get_db)):
    db.query(Cache).delete(synchronize_session=False)
    db.commit()
    return JSONResponse(content={"status": "ok"})


@app.get('/src/{item}')
async def assets(item: str):
    try:
        with open(f'page/{item}', 'rb') as fp:
            if item.endswith('html'):
                media_type = "text/html"
            elif item.endswith('css'):
                media_type = "text/css"
            else:
                media_type = "text/plain"
            return Response(
                content=fp.read(),
                status_code=200,
                media_type=media_type
            )
    except FileNotFoundError:
        return Response(status_code=404)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response
