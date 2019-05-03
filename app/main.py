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

template = Template()


def render_svg(**kwargs):
    fp = NamedTemporaryFile(
        mode='w+',
        dir='.',
        suffix='.tex',
        delete=False,
        encoding='utf8',
    )
    fp.write(template.render(**kwargs))
    name = basename(fp.name).split('.')[0]
    fp.close()

    bin_latex = template.latex_bin(**kwargs)
    run(f'{bin_latex} "{name}.tex"', shell=True)
    run(f'{bin_latex} "{name}.tex"', shell=True)
    run(f'{bin_latex} "{name}.tex"', shell=True)
    run(f'pdf2svg "{name}.pdf" "{name}.svg"', shell=True)
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
        doc_class: str = Query(
            default=wrap(template.default_documentclass),
            title='Latex Docuement Class',
            description='URL-safe base64 encoded docuement type'),
        doc_option: str = Query(
            default=wrap(template.default_documentoption),
            title='Latex Docuement Class Option',
            description='URL-safe base64 encoded docuement options'),
        preamble: str = Query(
            default=wrap(template.default_preamble),
            title='Latex Docuement Preamble',
            description='URL-safe base64 encoded preamble snippet'),
        content: str = Query(
            default=wrap(template.example_latex_code),
            title='Latex Code',
            description='URL-safe base64 encoded latex code'),
        engine: str = Query(
            default=wrap(template.default_engine),
            title='Latex Compiler',
            description='URL-safe base64 encoded latex compiler name'),
):
    return render_svg(**{key: unwrap(val) for key, val in locals().items()})
