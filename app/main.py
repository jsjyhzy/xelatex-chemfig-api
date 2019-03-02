from base64 import b64encode, urlsafe_b64decode
from os.path import basename
from subprocess import run
from tempfile import NamedTemporaryFile

from fastapi import FastAPI

app = app = FastAPI()

BIN_LATEX = "xelatex"
BIN_PDF2SVG = "pdf2svg"


def render_svg(packages, content):

    compile_seq = {
        'compile_latex':
        '%s "{name}.tex"' % BIN_LATEX,
        'convert':
        '%s "{name}.pdf" "{name}.svg"' % BIN_PDF2SVG,
        'clean':
        'rm "{name}.aux" "{name}.log" "{name}.pdf" "{name}.tex" "{name}.svg"'
    }

    template = r'''
    \documentclass{standalone}
    %s
    \begin{document}
    %s
    \end{document}
    '''

    fp = NamedTemporaryFile(
        mode='w+', dir='.', suffix='.tex', delete=False, encoding='utf8')
    fp.write(template % (packages, content))
    name = basename(fp.name).split('.')[0]
    fp.close()
    run(compile_seq['compile_latex'].format(name=name), shell=True)
    run(compile_seq['convert'].format(name=name), shell=True)
    with open(f'{name}.svg', 'rb') as fp:
        svg = fp.read()
    run(compile_seq['clean'].format(name=name), shell=True)
    return svg


def unwrap(wrapped):
    return urlsafe_b64decode(wrapped).decode('utf8')


def wrap(unwraped):
    return b64encode(unwraped)


@app.get('/svg')
def latex2svg(env: str, content: str):
    return {
        'content': wrap(render_svg(unwrap(env), unwrap(content))),
        'type': 'svg'
    }
