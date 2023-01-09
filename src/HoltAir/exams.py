import PyPDF2
import re
import os
from ._text_reading import get_results_from_text,document_check
from ._sleep_detection import detect_sleep
from ._statistics import ExamStatistics
import pdf2image
from ._image_reading import get_results_from_image, get_attributes,image_check
from ._exceptions import ExamNotFoundException,InvalidFileTypeException
import PIL
import numpy as np
import pytesseract
import pandas as pd
import urllib



class Exam:
    '''
    Exam abstract class which attributes will be inherited by ExamFromText and ExamFromImage
    :param scan_end_time: end time of an exam
    :param scan_start_time: start time of an exam
    :param results_df: data frame containing measure values from the exam
    :param  exam_statistics: ExamStatistics object with dataframes with calculated measures as attributes
    :param  patient: Patient object with the
    '''
    def __init__(self, filepath):
        self.scan_end_time = ""
        self.scan_start_time = ""
        self.results_df = None

        self._set_patient()
        self._set_exam_data()
        self.results_df['Sleep'], self.sleep_detection_method = detect_sleep(self.results_df)
        self.exam_statistics = ExamStatistics(self.results_df)

    def _set_exam_data(self):
        pass

    def _set_patient(self):
        pass


class ExamFromText(Exam):
    '''
    class that contains exam information that are read from pdf
    :param filepath: path to the pdf file
    :param reader: pdf reader from the PyPDF2 librarry
    '''
    def __init__(self, filepath):
        self.filepath = filepath
        with open(self.filepath, "rb") as f:
            self.reader = PyPDF2.PdfFileReader(f, "rb")
            if self.reader.numPages < 2:
                raise ExamNotFoundException()
            document_check(self.reader.getPage(0).extract_text(), self.reader.getPage(1).extract_text())
            super().__init__(filepath)

    def _set_exam_data(self):
        '''
        sets the values for the scan_start_time, scan_end_time and results_df attributes
        with the text extracted from first two pages of the pdf
        '''
        page_0 = self.reader.getPage(0)
        text_page_0 = page_0.extractText()
        text_arr_0 = text_page_0.split("\n")

        page_1 = self.reader.getPage(1)
        text_page_1 = page_1.extractText()
        self.scan_start_time = re.sub(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', '', text_arr_0[12].split("a:")[1].strip()).strip()
        self.scan_end_time = re.sub(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', '', text_arr_0[13].split("a:")[1].strip()).strip()
        self.results_df = get_results_from_text(text_page_1)

    def _set_patient(self):
        '''
        creates the patient object and fills the attributes with text extracted from first page of the pdf
        '''
        patient = Patient()
        page_0 = self.reader.getPage(0)
        text = page_0.extractText()
        text_arr = text.split("\n")
        if text_arr[1].split(":")[1].strip().split(",")[0] == '':
            n = len(text_arr)
            name = text_arr[n - 3].strip().split()[-1]
            patient.last_name = name.split(",")[0]
            patient.first_name = name.split(",")[1]
            patient.patient_id = text_arr[n - 2].strip()
            patient.birth_date = text_arr[n - 1].strip()
        else:
            patient.last_name = text_arr[1].split(":")[1].strip().split(",")[0]
            patient.first_name = text_arr[1].split(":")[1].strip().split(",")[1]
            patient.patient_id = text_arr[2].split(":")[1].strip()
            patient.birth_date = text_arr[3].split(":")[1].strip()
        self.patient = patient




class ExamFromImage(Exam):
    '''
    class that contains exam information that are read from not readable pdf using ocr
    :param filepath: path to the pdf file
    :param images: liost of the images extracted from the pdf file
    '''
    def __init__(self, filepath,popplerpath):
        self.filepath = filepath
        _, file_extension = os.path.splitext(filepath)
        # tmp solution
        if file_extension == '.pdf':
            self.images = pdf2image.convert_from_path(filepath, dpi=300,
                                                      poppler_path=popplerpath)
        else:
            img = PIL.Image.open(filepath)
            self.images = [_, np.asarray(img)]
        if len(self.images) < 2:
            raise ExamNotFoundException()
        image_check(self.images[0],self.images[1])
        super().__init__(filepath)

    def _set_exam_data(self):
        '''
        sets the values for the scan_start_time, scan_end_time and results_df attributes
        using images that contain first and second page of exam result
        '''
        self.results_df = get_results_from_image(self.images[1])
        attr = get_attributes(self.images[0])
        self.scan_start_time = attr['scan_start_time']
        self.scan_end_time = attr['scan_end_time']

    def _set_patient(self):
        '''
        creates the patient object and fills the attributes with data extracted from image of first page
        '''
        patient = Patient()
        attr = get_attributes(self.images[0])
        patient.first_name = attr['first_name']
        patient.last_name = attr['last_name']
        patient.patient_id = attr['patient_id']
        patient.birth_date = attr['birthdate']
        self.patient = patient


class Patient:
    '''
    contains information about the patient
    :param first_name: Patient first name
    :param last_tanme:  Patient second name
    :param patient_id: Patient ID
    :param birrthdate: Patient birthdate
    '''
    first_name = ""
    last_name = ""
    patient_id = ""
    birthdate = ""


def get_exam(filepath,popplerpath,tesseractpath):
    '''
    checks if text can be extracted from the pdf and creates adequate exam object
    :param filepath: path to the pdf file
    :param popplerpath: path to the poppler exe file
    :return: ExamFromText or ExamFromImage object
    '''
    _, file_extension = os.path.splitext(filepath)
    if file_extension == ".pdf":
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfFileReader(f, "rb")
            if reader.getPage(0).extract_text():
                return ExamFromText(filepath)
            else:
                return ExamFromImage(filepath)
    else:
        raise InvalidFileTypeException()