class LowDpiException(Exception):
    def __init__(self):
        self.message = "DPI of the image is to LOW, OCR will not return relying results."


class DataFrameColNumberException(Exception):
    def __init__(self):
        self.message = "OCR failed to read columns from table."


class NotNumericCharacterException(Exception):
    def __init__(self):
        self.message = "Cell value in numeric column is not numeric"


class DataFrameRowNumberException(Exception):
    def __init__(self):
        self.message = "OCR ommited rows while reading table."


class  InformationNotFoundException(Exception):
    def __init__(self):
        self.message = "OCR failed to recognize information field."


class InvalidFileTypeException(Exception):
    def __init__(self):
        self.message = "Invalid input file type."

class ExamNotFoundException(Exception):
    def __init__(self):
        self.message= "Exam not found on page"

class InvalidNumericValueException(Exception):
    def __init__(self):
        self.message = "OCR failed to recognize one of the cell values correctly."

class InsufficientObesrvationsException(Exception):
    def __init__(self):
        self.message = "Number of observations is insufficient for statistics to be calculated"