class Template:
    def __init__(self):
        import configparser
        from os.path import dirname, join
        config_file = join(dirname(__file__), 'app.ini')
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

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
    def example_latex_code(self):
        return self.config['example']['latex_code']