from base64 import b64decode, b64encode
from functools import reduce
from glob import glob
from json import loads
from lzma import LZMACompressor, LZMADecompressor
from os import remove
from subprocess import PIPE, Popen


def bcompress(b):
    if b is None:
        return None
    com = LZMACompressor()
    chunk = com.compress(b)
    tail = com.flush()
    return chunk+tail


def bdecompress(cb):
    if cb is None:
        return None
    com = LZMADecompressor()
    chunk = com.decompress(cb)
    return chunk


def b2c(b):
    if b is None:
        return None
    return b64encode(b).decode('utf8')


def unwrap(wrapped):
    return b64decode(wrapped).decode('utf8')


def wrap(unwarpped):
    return b64encode(unwarpped.encode('utf8'))


def compiling(exec_seq, context, workid):
    '''
    return stdout,stderr,attachment
    '''
    out, err = [], []
    with open(f'{workid}.tex', 'w+') as tex:
        tex.write(context)
    for seq in exec_seq:
        command = bytes(' '.join(['$']+seq), encoding='utf8')
        out.append(command)
        err.append(command)
        process = Popen(seq, stdout=PIPE, stderr=PIPE)
        o, e = process.communicate()
        out.append(o)
        err.append(e)
    try:
        with open(f'{workid}.o', 'rb') as attachment:
            att = attachment.read()
    except FileNotFoundError:
        att = None
    out = reduce(lambda x, y: x+b'\n'+y, out)
    err = reduce(lambda x, y: x+b'\n'+y, err)
    for aux in glob(f'{workid}.*'):
        remove(aux)
    return out, err, att


class Template:
    def __init__(self):
        import configparser
        from os.path import dirname, join
        config_file = join(dirname(__file__), 'app.ini')
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def content_type_jsons(self, jsons):
        kwargs = loads(jsons)
        return self.content_type(**kwargs)

    def content_type(self, **kwargs):
        target = kwargs.get('target', 'svg')
        if target == 'svg':
            return 'image/svg+xml'

    def assign_jsons(self, workid, jsons):
        kwargs = loads(jsons)
        return self.assign(workid, **kwargs)

    def assign(self, workid, **kwargs):
        compilepass = kwargs.get('compilepass', 3)
        target = kwargs.get('target', 'svg')
        engine = self.latex_bin(**kwargs)
        nohault = [engine, '-interaction=nonstopmode',
                   '-file-line-error', '-c-style-errors']
        if target == 'svg':
            return [[*nohault, f'{workid}.tex']]*compilepass + [['pdf2svg', f'{workid}.pdf', f'{workid}.o']]
        else:
            return [[*nohault, f'{workid}.tex']]*compilepass

    def render_jsons(self, jsons):
        kwargs = loads(jsons)
        for k, v in kwargs.items():
            try:
                v = unwrap(v)
                kwargs[k] = v
            except:
                pass
        return self.render(**kwargs)

    def render(self, **kwargs):
        documentclass = self.documentclass(
            doccls=kwargs.get('doc_class', None),
            docopt=kwargs.get('doc_option', None))
        preamble = self.preamble(preamble=kwargs.get('preamble', None), )

        content = kwargs.get('content')

        return '\n'.join([
            documentclass,
            preamble,
            '\\begin{document}',
            content,
            '\\end{document}',
        ])

    def documentclass(self, doccls, docopt):
        if doccls is None:
            doccls = self.default_documentclass
        if docopt is None:
            docopt = self.default_documentoption
        return '\\documentclass[%s]{%s}' % (docopt, doccls)

    def preamble(self, preamble):
        if preamble is None:
            preamble = self.default_preamble
        return preamble

    def latex_bin(self, **kwargs):
        engine = kwargs.get('engine')
        if engine.upper() == 'PDFLATEX':
            return 'pdflatex'
        if engine.upper() == 'LUALATEX':
            return 'lualatex'
        if engine.upper() == 'XELATEX':
            return 'xelatex'

        return 'pdflatex'

    @property
    def default_preamble(self):
        return self.config['options']['usepackage']

    @property
    def default_documentclass(self):
        return self.config['options']['documentclass']

    @property
    def default_documentoption(self):
        return self.config['options']['documentoption']

    @property
    def default_engine(self):
        return self.config['options']['engine']

    @property
    def example_latex_code(self):
        return self.config['example']['latex_code']

    @property
    def database_uri(self):
        return self.config['database']['uri']
