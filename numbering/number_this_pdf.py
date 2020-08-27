# kevinjel 2020
import logging
from pathlib import Path
from PyPDF2.pdf import PdfFileReader, PdfFileWriter
from reportlab.graphics import shapes
from reportlab.lib.colors import _CMYK_black as black
from reportlab.graphics import renderPDF
from reportlab.lib.units import mm, inch

from lib import args
import io
import copy

logging.basicConfig(format='%(asctime)s,%(msecs)d | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)

log = logging.getLogger(__name__)


def readfile(pfile):
    pfile = Path(pfile)
    in_f = open(pfile, "rb")
    return PdfFileReader(in_f)


def draw_number(w, h, nr):
    w, h = w*mm, h*mm
    d = shapes.Drawing(w, h)
    d.add(shapes.String(w/2, h/2, f"{nr}", textAnchor="middle",
                        fontSize=15, fillColor=black))
    return renderPDF.drawToString(d)


def add_number(p, n, x, y, counter=1):
    base_pdf = copy.copy(p.getPage(0))
    wm_pdf = PdfFileReader(io.BytesIO(n)).getPage(0)

    pdf_writer = PdfFileWriter()
    base_pdf.mergeTranslatedPage(wm_pdf, x, y)
    pdf_writer.addPage(base_pdf)

    saveloc = Path.cwd().joinpath("numbering", "assets",
                                  "numbered", f"{counter}.pdf")
    with open(saveloc, "wb") as outfile:
        pdf_writer.write(outfile)
    return


def main():
    u_args = args.cl_args()
    # where to put the watermark (bottom left, it is a guess tho)
    x, y = 200, 100
    # read template pdf
    pfile_obj = readfile(u_args.f[0])
    # set the total numbers and the leading zeroes
    amount_of_numbers = int(u_args.n[0])
    leading_zeroes = len(u_args.n[0])
    # loop trough numbers
    for nr in range(0, amount_of_numbers):
        # append leading zeroes to current number in loop
        nr_leading_zeroes = str(nr+1).zfill(leading_zeroes)
        # make watermark
        nr_pdf = draw_number(50, 30, str(nr_leading_zeroes))
        # add the watermark to the page
        add_number(pfile_obj, nr_pdf, x, y, nr_leading_zeroes)
    pass


if __name__ == "__main__":
    main()
    pass
