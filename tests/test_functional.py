import glob
import os
import re
import tempfile
import shutil

from sphinx.application import Sphinx

from nose.tools import *

_fixturedir = os.path.join(os.path.dirname(__file__), 'fixture')
_fakecmd = os.path.join(os.path.dirname(__file__), 'fakecmd.py')
_fakeepstopdf = os.path.join(os.path.dirname(__file__), 'fakeepstopdf.py')

def setup():
    global _tempdir, _srcdir, _outdir
    _tempdir = tempfile.mkdtemp()
    _srcdir = os.path.join(_tempdir, 'src')
    _outdir = os.path.join(_tempdir, 'out')
    os.mkdir(_srcdir)

def teardown():
    shutil.rmtree(_tempdir)

def readfile(fname):
    f = open(os.path.join(_outdir, fname), 'rb')
    try:
        return f.read()
    finally:
        f.close()

def runsphinx(text, builder, confoverrides):
    f = open(os.path.join(_srcdir, 'index.rst'), 'wb')
    try:
        f.write(text.encode('utf-8'))
    finally:
        f.close()
    app = Sphinx(_srcdir, _fixturedir, _outdir, _outdir, builder,
                 confoverrides)
    app.build()

def with_runsphinx(builder, **kwargs):
    confoverrides = {'plantuml': _fakecmd}
    confoverrides.update(kwargs)
    def wrapfunc(func):
        def test():
            src = '\n'.join(l[4:] for l in func.__doc__.splitlines()[2:])
            os.mkdir(_outdir)
            try:
                runsphinx(src, builder, confoverrides)
                func()
            finally:
                os.unlink(os.path.join(_srcdir, 'index.rst'))
                shutil.rmtree(_outdir)
        test.__name__ = func.__name__
        return test
    return wrapfunc

@with_runsphinx('html', plantuml_output_format='svg')
def test_buildhtml_simple_with_svg():
    """Generate simple HTML

    .. uml::

       Hello
    """
    pngfiles = glob.glob(os.path.join(_outdir, '_images', 'plantuml-*.png'))
    assert len(pngfiles) == 1
    svgfiles = glob.glob(os.path.join(_outdir, '_images', 'plantuml-*.svg'))
    assert len(svgfiles) == 1

    assert b'<img src="_images/plantuml' in readfile('index.html')
    assert b'<object data="_images/plantuml' in readfile('index.html')

    pngcontent = readfile(pngfiles[0]).splitlines()
    assert b'-pipe' in pngcontent[0]
    assert_equals(b'Hello', pngcontent[1][2:])
    svgcontent = readfile(svgfiles[0]).splitlines()
    assert b'-tsvg' in svgcontent[0]
    assert_equals(b'Hello', svgcontent[1][2:])

@with_runsphinx('html', plantuml_output_format='none')
def test_buildhtml_no_output():
    """Generate simple HTML with uml directive disabled

    .. uml::

       Hello
    """
    assert '<img ' not in readfile('index.html')

@with_runsphinx('html')
def test_buildhtml_samediagram():
    """Same diagram should be same file

    .. uml::

       Hello

    .. uml::

       Hello
    """
    files = glob.glob(os.path.join(_outdir, '_images', 'plantuml-*.png'))
    assert len(files) == 1
    imgtags = [l for l in readfile('index.html').splitlines()
               if b'<img src="_images/plantuml' in l]
    assert len(imgtags) == 2

@with_runsphinx('html')
def test_buildhtml_alt():
    """Generate HTML with alt specified

    .. uml::
       :alt: Foo <Bar>

       Hello
    """
    assert b'alt="Foo &lt;Bar&gt;"' in readfile('index.html')

@with_runsphinx('html')
def test_buildhtml_caption():
    """Generate HTML with caption specified

    .. uml::
       :caption: Caption with **bold** and *italic*

       Hello
    """
    assert (b'Caption with <strong>bold</strong> and <em>italic</em>'
            in readfile('index.html'))

@with_runsphinx('html')
def test_buildhtml_nonascii():
    u"""Generate simple HTML of non-ascii diagram

    .. uml::

       \u3042
    """
    files = glob.glob(os.path.join(_outdir, '_images', 'plantuml-*.png'))
    content = readfile(files[0]).splitlines()
    assert b'-charset utf-8' in content[0]
    assert_equals(u'\u3042', content[1][2:].decode('utf-8'))

@with_runsphinx('latex')
def test_buildlatex_simple():
    """Generate simple LaTeX

    .. uml::

       Hello
    """
    files = glob.glob(os.path.join(_outdir, 'plantuml-*.png'))
    assert len(files) == 1
    assert re.search(br'\\(sphinx)?includegraphics\{+plantuml-',
                     readfile('plantuml_fixture.tex'))

    content = readfile(files[0]).splitlines()
    assert b'-pipe' in content[0]
    assert_equals(b'Hello', content[1][2:])

@with_runsphinx('latex', plantuml_latex_output_format='eps')
def test_buildlatex_simple_with_eps():
    """Generate simple LaTeX with EPS

    .. uml::

       Hello
    """
    files = glob.glob(os.path.join(_outdir, 'plantuml-*.eps'))
    assert len(files) == 1
    assert re.search(br'\\(sphinx)?includegraphics\{+plantuml-',
                     readfile('plantuml_fixture.tex'))

    content = readfile(files[0]).splitlines()
    assert b'-teps' in content[0]
    assert_equals(b'Hello', content[1][2:])

@with_runsphinx('latex', plantuml_latex_output_format='pdf')
def test_buildlatex_simple_with_pdf():
    """Generate simple LaTeX with PDF

    .. uml::

       Hello
    """
    epsfiles = glob.glob(os.path.join(_outdir, 'plantuml-*.eps'))
    pdffiles = glob.glob(os.path.join(_outdir, 'plantuml-*.pdf'))
    assert len(epsfiles) == 1
    assert len(pdffiles) == 1
    assert re.search(br'\\(sphinx)?includegraphics\{+plantuml-',
                     readfile('plantuml_fixture.tex'))

    epscontent = readfile(epsfiles[0]).splitlines()
    assert b'-teps' in epscontent[0]
    assert_equals(b'Hello', epscontent[1][2:])

@with_runsphinx('latex', plantuml_latex_output_format='none')
def test_buildlatex_no_output():
    """Generate simple LaTeX with uml directive disabled

    .. uml::

       Hello
    """
    assert not re.search(br'\\(sphinx)?includegraphics\{+plantuml-',
                         readfile('plantuml_fixture.tex'))

@with_runsphinx('latex')
def test_buildlatex_with_caption():
    """Generate LaTeX with caption

    .. uml::
       :caption: Hello UML

       Hello
    """
    out = readfile('plantuml_fixture.tex')
    assert re.search(br'\\caption\{\s*Hello UML\s*\}', out)
    assert re.search(br'\\begin\{figure\}\[htbp\]', out)
    assert not re.search(br'\\begin\{flushNone', out)  # issue #136

@with_runsphinx('latex')
def test_buildlatex_with_align():
    """Generate LaTeX with caption

    .. uml::
       :align: right

       Hello
    """
    out = readfile('plantuml_fixture.tex')
    assert (re.search(br'\\begin\{figure\}\[htbp\]\\begin\{flushright\}', out)
            or re.search(br'\\begin\{wrapfigure\}\{r\}', out))

@with_runsphinx('pdf')
def test_buildpdf_simple():
    """Generate simple PDF

    .. uml::

       Hello
    """
    epsfiles = glob.glob(os.path.join(_outdir, 'plantuml-*.eps'))
    pdffiles = glob.glob(os.path.join(_outdir, 'plantuml-*.pdf'))
    assert len(epsfiles) == 1
    assert len(pdffiles) == 1

    epscontent = readfile(epsfiles[0]).splitlines()
    assert b'-teps' in epscontent[0]
    assert_equals(b'Hello', epscontent[1][2:])
