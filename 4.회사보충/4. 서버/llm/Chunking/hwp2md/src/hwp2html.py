import fire

from hwp5.hwp5html import HTMLTransform
from hwp5.dataio import ParseError
from hwp5.errors import InvalidHwp5FileError
from hwp5.utils import make_open_dest_file
from hwp5.xmlmodel import Hwp5File
from contextlib import closing

from util import logger

def hwp2html(hwp5path='MOA_MOB.hwp', 
             destpath='MOA_MOB.html'):
    logger.info(f'hwp5path: {hwp5path}, destpath: {destpath}')
    
    def wrap_for_xml(open_dest):
        from hwp5.utils import wrap_open_dest_for_tty
        from hwp5.utils import pager
        from hwp5.utils import syntaxhighlight
        from hwp5.utils import xmllint
        return wrap_open_dest_for_tty(open_dest, [
            pager(),
            syntaxhighlight('application/xml'),
            xmllint(format=True, nonet=True),
        ])
    
    html_transform = HTMLTransform()

    open_dest = make_open_dest_file(destpath)

    transform = html_transform.transform_hwp5_to_xhtml
    open_dest = wrap_for_xml(open_dest)

    try:
        with closing(Hwp5File(hwp5path)) as hwp5file:
            with open_dest() as dest:
                transform(hwp5file, dest)
    except ParseError as e:
        print(e)


if __name__ == '__main__':
    fire.Fire(hwp2html)