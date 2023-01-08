## Project description
HoltAir is a tool for python that reads and analyzes data from Holter blood pressure test results in PDF format.
## Usage

### Quickstart:  
```python
from holtair import exams

# you have to specify the tesseract executable in your PATH:
tesseract_path = r'<full_path_to_your_tesseract_executable>'
#also you have to specify the pdf2image poppler executable in your PATH:
poppler_path =  r'<full_path_to_your_poppler_executable>'

#create Exam object with test result data
exam = exams.get_exam(r'test_file.pdf',poppler_path,tesseract_path)

#get pandas dataframe with raw data  
print(exam.results_df)

#create ExamStatistics object calculated statistics 
statistics = exam.exam_statistics

#get basic statistics such sa mean,std,min and max for different blood pressure indicators
print(statistics.basic_overall)

# get basic statistics for detected night:
print(statistics.basic_night)

# create Patient with information about patient
patient = exam.patient

# get patient id 
print(patient.patient_id)
```

## Necessary files:  
Windows
* Poppler: https://github.com/oschwartz10612/poppler-windows/releases/
* Tesseract https://github.com/UB-Mannheim/tesseract/wiki  

Linux
* Poppler (using conda):` conda install -c conda-forge poppler`
* Tesseract : `sudo apt install tesseract-ocr`,
`sudo apt install libtesseract-dev `

## Functions and classes description

### get_exam() function
This function is used to return the ExamFromImage or ExamFromText object that contain all the analysis and test results data.  

Parameters:  
`get_exam(fielpath,popplerpath,tesseractpath)`
* **filepath** Path to the PDF file containing the exam result.
* **popplerpath** Path to the poppler executable used in the pdf2image package.
* **tesseractpath** Path to the Tesseract executable used in pytesseract package.



### Exam class
ExamFromImage and ExamFromText inherit from Exam class. Their objects store all the analysis and information data regarding 
test result. ExamFromText object contains exam information that is read directly from the pdf file and ExamFromImage object contains the information that is read from not readable pdf using Tesseract OCR.   

Attributes:
* **results_df** Dataframe containing measure values from the exam.
* **exam_statistics** ExamStatistics object storing dataframes with calculated statistics. 
* **patient** Patient object which stores data about patient.
* **scan_end_time** String value with time of the end of the exam.
* **scan_start_time** String value with time of the start of the exam.

### ExamStatistics class
ExemStatistics objects stores dataframes with calculated statistics from data from exam results for day, night, both 
and dictionary with pb_load values.   

Attributes:
* **basic_overall** Dataframe with statistics for day and night.
* **basic_day** Dataframe with  basic statistics for a  day.
* **basic_night** Dataframe with  basic statistics for a night.
* **param bp_load** Dictionary with pb_load values for day, night and joined.

### Patient 
Patient object stores the basic information about the patient.  

Attributes:
* **first_name** Patient first name.
* **last_name**  Patient second name.
* **patient_id** Patient ID.
* **birrthdate** Patient birthdate.

    
    






