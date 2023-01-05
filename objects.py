import PyPDF2
import re
import os


from .utils import get_results_from_text,document_check
from .sleep_detection import detect_sleep
from .statistics import ExamStatistics
import pdf2image
from .ocr import get_results_from_image, get_attributes,image_check
from .exceptions import ExamNotFoundException
import PIL
import numpy as np
import pandas as pd
import urllib



class Exam:
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

    def __init__(self, filepath):
        self.filepath = filepath
        fhandle = open(self.filepath, 'rb')
        self.reader = PyPDF2.PdfFileReader(fhandle)
        if self.reader.numPages < 2:
            raise ExamNotFoundException()
        document_check(self.reader.getPage(0).extract_text(), self.reader.getPage(1).extract_text())
        super().__init__(filepath)

    def _set_exam_data(self):
        page_0 = self.reader.getPage(0)
        text_page_0 = page_0.extractText()
        text_arr_0 = text_page_0.split("\n")

        page_1 = self.reader.getPage(1)
        text_page_1 = page_1.extractText()

        # self.doctor = text_arr_0[9].split(":")[1].strip()
        # self.technician = text_arr_0[10].split(":")[1].strip()
        # self.duration = text_arr_0[11].split("a:")[1].strip()
        self.scan_start_time = re.sub(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', '', text_arr_0[12].split("a:")[1].strip()).strip()
        self.scan_end_time = re.sub(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', '', text_arr_0[13].split("a:")[1].strip()).strip()

        # tmp_string = text_arr_0[14]
        # self.succesful_measurements = tmp_string.split(":")[1][0:4].strip()
        # self.pct_succesful_measurements = tmp_string[tmp_string.find("%") - 3:tmp_string.find("%")].strip()

        self.results_df = get_results_from_text(text_page_1)

    def _set_patient(self):
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

    def __init__(self, filepath):
        self.filepath = filepath
        _, file_extension = os.path.splitext(filepath)
        # tmp solution
        if file_extension == '.pdf':
            self.images = pdf2image.convert_from_path(filepath, dpi=300,
                                                      poppler_path=r"C:\user\src\app\poppler-22.04.0\Library\bin")
        else:
            img = PIL.Image.open(filepath)
            self.images = [_, np.asarray(img)]
        if len(self.images) < 2:
            raise ExamNotFoundException()
        image_check(self.images[0],self.images[1])
        super().__init__(filepath)

    def _set_exam_data(self):
        self.results_df = get_results_from_image(self.images[1])
        attr = get_attributes(self.images[0])
        self.scan_start_time = attr['scan_start_time']
        self.scan_end_time = attr['scan_end_time']

    def _set_patient(self):
        patient = Patient()
        attr = get_attributes(self.images[0])
        patient.first_name = attr['first_name']
        patient.last_name = attr['last_name']
        patient.patient_id = attr['patient_id']
        patient.birth_date = attr['birthdate']
        self.patient = patient


class Patient:
    first_name = ""
    last_name = ""
    patient_id = ""
    birthdate = ""
    # sex = ""
    # height = ""
    # weight = ""
    # race = ""