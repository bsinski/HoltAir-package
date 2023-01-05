import pandas as pd
import re
import datetime
from .exceptions import ExamNotFoundException

def get_results_from_text(text: str) -> pd.DataFrame:
    '''
    :param text: text from Page 1 containing table with exam results
    :return: df with results
    '''

    text_arr = text.split("\n")

    # extract rows starting with measurement number
    text_arr = [x for x in text_arr if re.match("^\d{1,2}", x)]

    # save annotations
    annotation_column = []
    ANNOTATIONS = ["P", "R", "EZ", "ER", "EA", "<>"]
    for text in text_arr:
        sliced = ""
        if re.search("[A-Za-z<>]", text):
            first_letter_index = re.search("[A-Za-z<>]", text).start()
            sliced = text[first_letter_index:first_letter_index + 1].strip()
        if sliced and sliced in ANNOTATIONS:
            annotation_column.append(sliced)
        else:
            annotation_column.append("")

    # remove any letters
    text_arr = [re.sub(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', '', x) for x in text_arr]

    # remove double whitespaces
    text_arr = [re.sub(' +', ' ', x) for x in text_arr]

    # filter garbage at the end of the lines
    text_arr = [x.split(" ")[0:7] for x in text_arr]

    # create data frame
    df = pd.DataFrame(text_arr)
    df.columns = ["#", "Czas", "Sys", "Dia", "SCT", "PP", "HR"]
    df[["#", "Sys", "Dia", "SCT", "PP", "HR"]] = df[["#", "Sys", "Dia", "SCT", "PP", "HR"]].astype('int')
    df["_"] = annotation_column
    df=df[["#", "_", "Czas", "Sys", "Dia", "SCT", "PP", "HR"]]

    return df


# metoda zmieniającą rodzaj kolumny czasu na datetime z datą 01.01.1900 i 02.01.1900 jeżeli następuje w badaniu nowy dzień
def transform_to_time(column):
    list_with_time = pd.to_datetime(column,format='%H:%M').tolist()
    days_to_add = datetime.timedelta(days=0)
    for i in range(len(list_with_time)):
        if list_with_time[i] < list_with_time[i-1]:
            days_to_add = datetime.timedelta(days=1)
        newtime = list_with_time[i] + days_to_add
        list_with_time[i] = newtime.to_pydatetime()
    return list_with_time

def document_check(page0_text,page1_text):
    if re.search('Informacje o pacjencie',page0_text) is None or re.search('ZESTAWIENIE DANYCH SUROWYCH',page1_text) is None:
        raise ExamNotFoundException()
    return