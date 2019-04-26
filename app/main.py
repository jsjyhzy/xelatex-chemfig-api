from base64 import urlsafe_b64decode, urlsafe_b64encode
from os.path import basename
from subprocess import run
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, Query
from starlette.responses import Response

try:
    from .utils import Template
except ImportError:
    from utils import Template

app = FastAPI()

BIN_LATEX = "xelatex"
BIN_PDF2SVG = "pdf2svg"

template = Template()


def render_svg(packages, content):
    fp = NamedTemporaryFile(
        mode='w+',
        dir='.',
        suffix='.tex',
        delete=False,
        encoding='utf8',
    )
    fp.write(template.render(packages=packages, content=content))
    name = basename(fp.name).split('.')[0]
    fp.close()

    run(f'{BIN_LATEX} "{name}.tex"', shell=True)
    run(f'{BIN_PDF2SVG} "{name}.pdf" "{name}.svg"', shell=True)
    with open(f'{name}.svg', 'rb') as fp:
        svg = fp.read()
    names = ' '.join(
        [f'"{name}.{ext}"' for ext in ['aux', 'log', 'pdf', 'tex', 'svg']])
    run(f'rm {names}', shell=True)
    return Response(
        content=svg,
        status_code=200,
        headers=None,
        media_type='image/svg+xml',
    )


def unwrap(wrapped):
    return urlsafe_b64decode(wrapped).decode('utf8')

def wrap(unwarpped):
    return urlsafe_b64encode(unwarpped.encode('utf8'))


@app.get('/svg', content_type=Response(media_type='image/svg+xml'))
async def latex2svg(
        env: str = Query(
            default=wrap(template.default_preamble),
            title='Latex Docuement Preamble',
            description='URL-safe base64 encoded preamble snippet',
            regex='^[0-9A-Za-z_\-]+=*$'),
        content: str = Query(
            default=wrap(template.example_latex_code),
            title='Latex Code',
            description='URL-safe base64 encoded latex code',
            regex='^[0-9A-Za-z_\-]+=*$'),
):
    return render_svg(unwrap(env), unwrap(content))

