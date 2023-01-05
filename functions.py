import PyPDF2
from .objects import ExamFromText, ExamFromImage
import os
from .exceptions import *

#initializes exam from filepath - fromImage or fromText based on the file provided
def get_exam(filepath):

    _, file_extension = os.path.splitext(filepath)
    if file_extension == ".pdf":
        fhandle = open(filepath, 'rb')
        reader = PyPDF2.PdfFileReader(fhandle)
        if reader.getPage(0).extract_text():
            return ExamFromText(filepath)
        else:
            return ExamFromImage(filepath)
    else:
        raise InvalidFileTypeException()
