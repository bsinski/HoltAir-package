# Project description
HoltAir is a tool for python that reads and analyzes data from Holter blood pressure test results in PDF format.
# USAGE

Quickstart:  
```python
from holtair import exams

# you have to specify the tesseract executable in your PATH:
tesseract_path = r'<full_path_to_your_tesseract_executable>'
#also you have to specify the pypdf2 poppler executable in your PATH:
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

### get_exam() function
This function is used to return the ExamFromImage or ExamFromText object that contatin all of the analysis and test results data.  
Parameters:  
`get_exam(fielpath,popplerpath,tesseractpath)`
* **filepath** 


