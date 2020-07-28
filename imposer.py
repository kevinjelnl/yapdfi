import sys
import logging
import math
from pathlib import Path
from pydantic import BaseModel
from typing import *

import PyPDF2
from reportlab.lib.units import mm, inch

logging.basicConfig(format='%(asctime)s,%(msecs)d | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)

log = logging.getLogger(__name__)
pt2mm = 0.3527777778


class Imposition(BaseModel):
    substrate_width:    float
    substrate_height:   float
    impose_width:       Optional[float]
    impose_height:      Optional[float]

    gutter:             Optional[int] = 5
    pages:              Optional[int] = 2
    up:                 Optional[int]
    orientation:        Optional[str] = "landscape"
    amount_x:           Optional[int]
    amount_y:           Optional[int]

    def set_orientation(self):
        sub_size = [self.substrate_height, self.substrate_width]
        if self.orientation == "landscape":
            # on landscape width should be larger then height
            if not self.substrate_width < self.substrate_height:
                sub_size[0] = self.substrate_width
                sub_size[1] = self.substrate_height
        else:
            # if orientation == portrait
            if self.substrate_height < self.substrate_width:
                sub_size[0] = self.substrate_width
                sub_size[1] = self.substrate_height

        self.substrate_width = sub_size[0]
        self.substrate_height = sub_size[1]
        return

    def upcalc(self, PDFw, PDFh):
        # add gutter to pdf
        pdf_gut_w = PDFw + self.gutter
        pdf_gut_h = PDFh + self.gutter
        # copied from our upcalc-api
        subw = self.substrate_width
        subh = self.substrate_height
        # landscape imposition
        landscape_w = math.floor(subw / pdf_gut_w)
        landscape_h = math.floor(subh / pdf_gut_h)
        landscape_up = math.floor(landscape_w * landscape_h)

        # calculate the portrait impose
        portrait_w = math.floor(subw / pdf_gut_h)
        portrait_h = math.floor(subh / pdf_gut_w)
        portrait_up = math.floor(portrait_w * portrait_h)

        if landscape_up > portrait_up:
            self.orientation = "landscape"
            self.amount_x = landscape_w
            self.amount_y = landscape_h
            self.up = landscape_up
        else:
            self.orientation = "portrait"
            self.amount_x = portrait_w
            self.amount_y = portrait_h
            self.up = portrait_up

        # calc the impose w & height
        self.impose_width = self.amount_x * pdf_gut_w
        self.impose_height = self.amount_y * pdf_gut_h

        # reset the orientation
        self.set_orientation()
        return

    def impose(self, pdfobj):
        pdf_writer = PyPDF2.PdfFileWriter()

        row_height = (pdfobj.trim_height+self.gutter)*mm  # 55mm
        single_width = (pdfobj.trim_width+self.gutter)*mm  # 85mm

        with open("./outfile.pdf", "wb") as pdf_to_write:
            for page in range(0, self.pages):
                # get the current pdf page
                cur_page = pdfobj.pdf_reader.getPage(page)
                # make the imposition sheet
                impsheet = PyPDF2.pdf.PageObject.createBlankPage(
                    None,  self.impose_width*mm, self.impose_height*mm)

                for y in range(0, self.amount_y):
                    cur_height = row_height*y
                    for x in range(0, self.amount_x):
                        impsheet.mergeTranslatedPage(
                            cur_page, single_width*x, cur_height)
                pdf_writer.addPage(impsheet)
            pdf_writer.write(pdf_to_write)
        return


class PDF(BaseModel):
    location:           Path
    trim_width:         Optional[float]
    trim_height:        Optional[float]
    pages:              Optional[int] = 2
    pdf_handle:         Optional[Any]
    pdf_reader:         Optional[Any]

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.read_pdf()
        return

    def read_pdf(self):
        self.pdf_handle = open(f"{self.location}", "rb")
        self.pdf_reader = PyPDF2.PdfFileReader(self.pdf_handle)
        self.pages = self.pdf_reader.getNumPages()
        # note:  this pulls only trimbox info from the first page
        trim_width = self.pdf_reader.getPage(0).trimBox.getWidth()
        trim_height = self.pdf_reader.getPage(0).trimBox.getHeight()

        # cleanup the format
        self.trim_width = round(float(trim_width) * pt2mm + 0.001, 2)
        self.trim_height = round(float(trim_height) * pt2mm + 0.001, 2)
        return

    def __del__(self):
        self.pdf_handle.close()
        return


def main():
    pdf = Path(sys.argv[1])
    log.debug(f"given pdf: {pdf}")
    pdfobj = PDF(location=pdf)
    impdata = {
        "substrate_width":  460,
        "substrate_height": 320,
        "pages":            pdfobj.pages
    }
    imp = Imposition(**impdata)
    imp.upcalc(PDFw=pdfobj.trim_width, PDFh=pdfobj.trim_height)
    imp.impose(pdfobj)
    del(pdfobj)
    pass


if __name__ == "__main__":
    main()
    pass
