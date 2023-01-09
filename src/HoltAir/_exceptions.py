class LowDpiException(Exception):
    '''
    exception used when height and width of the image is too small to resize the image with good quality
    '''
    def __init__(self):
        self.message = "DPI of the image is to LOW, OCR will not return relying results."


class DataFrameColNumberException(Exception):
    '''
    exception used when number of columns in dataframe from image reading is not 8 which is the right number
    '''
    def __init__(self):
        self.message = "OCR failed to read columns from table."


class NotNumericCharacterException(Exception):
    '''
     exception used when there is non-numeric value in dataframe column which should have only numeric values
    '''
    def __init__(self):
        self.message = "Cell value in numeric column is not numeric"


class DataFrameRowNumberException(Exception):
    '''
    exception when not every column in dataframe from image reading has the same number of rows
    '''
    def __init__(self):
        self.message = "OCR ommited rows while reading table."


class  InformationNotFoundException(Exception):
    '''
    exception when information about patient and exam could not be extracted from image
    '''
    def __init__(self):
        self.message = "OCR failed to recognize information field."


class InvalidFileTypeException(Exception):
    '''
    exception when user puts other file type than pdf in the system
    '''
    def __init__(self):
        self.message = "Invalid input file type."

class ExamNotFoundException(Exception):
    '''
    exception when exam results where not found in the pdf file delivered by user
    '''
    def __init__(self):
        self.message= "Exam not found on page"

class InvalidNumericValueException(Exception):
    '''
    exception when values in dataframe from image reading has impossible values created by
    mistake in character recognition
    '''
    def __init__(self):
        self.message = "OCR failed to recognize one of the cell values correctly."

class InsufficientObesrvationsException(Exception):
    '''
    exception when there are no values in day or night so the statistics calculating differences between
    day and night blood pressure values could not be calculated
    '''
    def __init__(self):
        self.message = "Number of observations is insufficient for statistics to be calculated"