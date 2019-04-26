class Template:
    def __init__(self):
        import configparser
        from os.path import dirname, join
        config_file = join(dirname(__file__), 'app.ini')
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def render(self, **kwargs):
        documentclass = self.documentclass(
            doccls=kwargs.get('documentclass', None), )
        preamble = self.preamble(packages=kwargs.get('packages', None), )

        content = kwargs.get('content')

        return '\n'.join([
            documentclass,
            preamble,
            '\\begin{document}',
            content,
            '\\end{document}',
        ])

    def documentclass(self, doccls):
        if doccls is None:
            doccls = self.default_documentclass
        return '\\documentclass{%s}' % doccls

    def preamble(self, packages):
        if packages is None:
            packages = self.default_preamble
        usepackage = '\n'.join(
            ['\\usepackage{%s}' % line for line in packages.split('\n')])

        return usepackage

    @property
    def default_preamble(self):
        return self.config['options']['usepackage']

    @property
    def default_documentclass(self):
        return self.config['options']['documentclass']

    @property
    def example_latex_code(self):
        return self.config['example']['latex_code']