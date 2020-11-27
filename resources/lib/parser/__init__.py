from importlib import import_module
from inspect import isclass
from pathlib import Path
from pkgutil import iter_modules

try:
    import lxml.etree


    class Parser(object):
        def parse(self, text):
            return lxml.etree.HTML(text, lxml.etree.HTMLParser(target=self))

except ImportError:
    import html.parser


    class Parser(html.parser.HTMLParser):
        def error(self, message):
            pass

        def handle_data(self, data):
            self.data(data)

        def handle_endtag(self, tag):
            self.end(tag)

        def handle_starttag(self, tag, attrs):
            self.start(tag, dict(attrs))

        def parse(self, text):
            self.feed(text)
            return self.close()

for module_info in iter_modules([Path(__file__).parent]):
    module = import_module(f"{__name__}.{module_info.name}")

    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)

        if isclass(attribute) and issubclass(attribute, Parser):
            globals()[attribute_name] = attribute
