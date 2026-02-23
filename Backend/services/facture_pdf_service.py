import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from sqlalchemy.orm import Session
from Backend import models

PAGE_HEIGHT = 841.89

def generer_facture_pdf(db: Session, facture_id: int):
    #Protected to assure client NDA contract confidentiality
    pass
  