# Trích bảng từ PDF
import unicodedata

# Hàm trích xuất thông tin học vị
import unicodedata
import re

import os
import json
import io
import fitz  # PyMuPDF
#import pytesseract
import pdfplumber
from PIL import Image
from tkinter import Tk, Button, filedialog, scrolledtext, messagebox, BOTH, WORD
import tkinter as tk

#pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
#os.environ['TESSDATA_PREFIX'] = r"C:\\Program Files\\Tesseract-OCR\\tessdata"
