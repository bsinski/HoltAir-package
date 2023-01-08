import cv2
import nltk
from sklearn.cluster import AgglomerativeClustering
from pytesseract import Output
import pandas as pd
import numpy as np
import imutils
import homoglyphs
import re
import pytesseract
from ._exceptions import *

# here give the path to the Tessercact engine executable file
#pytesseract.pytesseract.tesseract_cmd = r'C:\user\src\app\Tesseract-OCR\tesseract.exe'
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


###### Table reading ######

def get_results_from_image(img):
    '''
    joins all the methods from the module and perform recognition of table from image
    :param img: image in form of numpy arrays or PIL image object
    :return: resized image in form of numpy arrays
    '''
    img = np.array(img)
    dataframes = extract_tables(img.copy(), 90, 0, 1)
    return join_dataframes(dataframes)


def resizing(img):
    '''
    resizes the image so the DPI of the image is higher
    :param img: image in form of numpy arrays
    :return: resized image in form of numpy arrays
    '''
    shp = img.shape
    if shp[0] < 2500 and shp[1] < 2300:
        if shp[0] < 1194 or shp[1] < 1150:
            raise LowDpiException()
        return cv2.resize(img, (2388, 2688))
    else:
        return img


def color_and_treshold(image):
    '''
    changes the color af the image to black and white and performs a binarization of pixel values
    :param img: image in form of numpy arrays
    :return: preprocessed image in form of numpy arrays
    '''
    grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    tresh = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return tresh


def treshold(image):
    '''
    creates the blobs of text
    :param img: image in form of numpy arrays
    :return: image with blobs instead of characters
    '''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (80, 12))
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    grad = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    grad = np.absolute(grad)
    (minVal, maxVal) = (np.min(grad), np.max(grad))
    grad = (grad - minVal) / (maxVal - minVal)
    grad = (grad * 255).astype("uint8")
    grad = cv2.morphologyEx(grad, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return cv2.dilate(thresh, None, iterations=3)


def get_table(thresh, image):
    '''
     finds the table by choosing the area with biggest continuous blob
     :param tresh: image with blobs
     :param image: original image
     :return: cropped original image with table area and preprocessed with color_and_treschold() function
    '''
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    tableCnt = max(cnts, key=cv2.contourArea)
    (x, y, w, h) = cv2.boundingRect(tableCnt)
    table = image[y:y + h, x:x + w]
    return color_and_treshold(table)


def split_table(table):
    '''
    splits the table into two parts that later will be joined vertically
    :param table: image with table in form of numpy arrays
    :return: cropped original image
    '''
    width = table.shape[1]
    width_cutoff = width // 2
    table1 = table[:, :width_cutoff]
    table2 = table[:, width_cutoff:]
    return table1, table2


def perform_clustering(table, dist_tresh, min_size, min_conf, options):
    '''
    splits the table into two parts that later will be joined vertically
    :param table: image with table in form of numpy arrays
    :param dist_trash: distance treshold to limit the number of cluster
    :param min_size: the minimum number of observation to form a cluster
    :param min_size: the minimum confidence value for OCR to recognize te character
    :param options: options for the OCR engine such as page segmentation mode (PSM)
    :return df: dataframe with recognized column and values in cells
    :return table: table image with marked areas of recognized character and colored to visualize clusters
    '''
    # reading every character from the table
    results = pytesseract.image_to_data(
        table,
        config=options,
        output_type=Output.DICT)
    coords = []
    ocrText = []
    for i in range(0, len(results["text"])):
        x = results["left"][i]
        y = results["top"][i]
        w = results["width"][i]
        h = results["height"][i]
        text = results["text"][i]
        conf = int(float(results["conf"][i]))
        if conf > min_conf and text != '|':
            coords.append((x, y, w, h))
            ocrText.append(text)
    xCoords = [(c[0], 0) for c in coords]
    clustering = AgglomerativeClustering(
        n_clusters=None,
        affinity="manhattan",
        linkage="complete",
        distance_threshold=dist_tresh)
    # clustering character by x coordinate
    clustering.fit(xCoords)
    sortedClusters = []
    # sorting the clusters by x coordinate
    for l in np.unique(clustering.labels_):
        idxs = np.where(clustering.labels_ == l)[0]
        if len(idxs) > min_size:
            avg = np.average([coords[i][0] for i in idxs])
            sortedClusters.append((l, avg))
    sortedClusters.sort(key=lambda x: x[1])
    df = pd.DataFrame()
    # creating borderlines around characters in colors matching the clusters
    for (l, _) in sortedClusters:
        idxs = np.where(clustering.labels_ == l)[0]
        yCoords = [coords[i][1] for i in idxs]
        sortedIdxs = idxs[np.argsort(yCoords)]
        color = np.random.randint(0, 255, size=(3,), dtype="int")
        color = [int(c) for c in color]
        for i in sortedIdxs:
            (x, y, w, h) = coords[i]
            cv2.rectangle(table, (x, y), (x + w, y + h), color, 2)
        # saving the result to dataframe
        cols = [ocrText[i].strip() for i in sortedIdxs]
        currentDF = pd.DataFrame({cols[0]: cols[1:]})
        df = pd.concat([df, currentDF], axis=1)
    return df, table


def extract_tables(img, dist_tresh, min_size, min_conf):
    '''
    joins prevoius method and performs image preprocessing, table detection, character recognition, and clustering
    :param img: image in form of numpy arrays
    :param dist_trash: distance treshold to limit the number of cluster
    :param min_size: the minimum number of observation to form a cluster
    :param min_size: the minimum confidence value for OCR to recognize te character
    :return: typle of dataframes from both sides of page on recognized by two page segmentation modes
    '''
    imgr = resizing(img)
    tresh = treshold(imgr)
    table = get_table(tresh, imgr)
    (table1, table2) = split_table(table)
    # reading data with two page segmentation methods 6 and 11
    (df1, ntable1) = perform_clustering(table1.copy(), dist_tresh, min_size, min_conf, "--psm 11")
    (df2, ntable2) = perform_clustering(table2.copy(), dist_tresh, min_size, min_conf, "--psm 11")
    (df12, ntable12) = perform_clustering(table1.copy(), dist_tresh, min_size, min_conf, "--psm 6")
    (df22, ntable22) = perform_clustering(table2.copy(), dist_tresh, min_size, min_conf, "--psm 6")
    return df1, df2, df12, df22


def clear_output_11psm(df_in):
    '''
    from the table recognized with PSM 11 we keep all the column except number of measurement column
    and annotation column also cleans the result of invalid special characters
    :param df_in: original dataframe recognized with PSM 11
    :return: cleaned and cropped dataframe
    '''
    df_test = df_in.copy()
    df_test = df_test.dropna(axis=1, how='all')
    i = 0
    n = len(df_test.columns)
    while i < n:
        if nltk.edit_distance(df_test.columns[i],'Aktywnosc') <= 3:
            df_test = df_test.drop(columns=df_test.columns[i], axis=1)
            n -=1
            continue
        if nltk.edit_distance(df_test.columns[i],'Dziennika') <= 3:
            df_test = df_test.drop(columns=df_test.columns[i], axis=1)
            n -=1
            continue
        if nltk.edit_distance(df_test.columns[i],'Aktwnosc Dziennika') <= 5:
            df_test = df_test.drop(columns=df_test.columns[i], axis=1)
            n -=1
            continue
        i += 1
    df_test = df_test.replace({'\(|\)|\||\{|\}': ''}, regex=True)
    df_test = df_test.drop(columns=df_test.columns[0], axis=1)

    # if time is found in column name then it should be moved as cell value
    if re.search('\d{2}:\d{2}', df_test.columns[0]) is not None:
        times = [df_test.columns[0]] + df_test.iloc[:, 0].dropna().tolist()
    else:
        times = df_test.iloc[:, 0].dropna().tolist()
    df_test.drop(columns=df_test.columns[0], axis=1, inplace=True)
    if 'Czas' in df_test:
        df_test.drop(columns='Czas', axis=1, inplace=True)
    df_test = df_test.dropna(axis=0, how='all')
    # creating column with valida time values
    for t in times:
        if re.search('\d{2}:\d{2}', t) is None:
            times.remove(t)
    df = pd.concat([pd.DataFrame({'Czas': times}), df_test], axis=1)

    #make sure column names are correct
    try:
        df.columns = ['Czas','Sys', 'Dia', 'SCT', 'PP', 'HR']
    except ValueError:
        print(df)
        raise DataFrameColNumberException

    # use homoglyphs for 0 and 1
    h = homoglyphs.Homoglyphs()
    homoglyphs_for0 = '['+''.join(h.get_combinations('0'))+']'
    homoglyphs_for1 = '['+''.join(h.get_combinations('1'))+']'

    number_cols = ['Czas','Sys', 'Dia', 'SCT', 'PP', 'HR']
    df[number_cols] = df[number_cols].replace("[\(\)\{\}\[\]]", "", regex=True)
    df[number_cols] = df[number_cols].replace("[Iil\|\!]", "1", regex=True)
    df[number_cols] = df[number_cols].replace(homoglyphs_for0, "0", regex=True)
    df[number_cols] = df[number_cols].replace(homoglyphs_for1, "1", regex=True)
    df[number_cols] = df[number_cols].replace("[Oo]", "0", regex=True)
    df[number_cols] = df[number_cols].replace("[A]", "4", regex=True)
    df[number_cols] = df[number_cols].replace("[G]", "6", regex=True)
    df[number_cols] = df[number_cols].replace("[H]", "11", regex=True)
    df[number_cols] = df[number_cols].replace("[S]", "5", regex=True)
    df[number_cols] = df[number_cols].replace("[&B]", "8", regex=True)
    for i in range(df.shape[0]):
        for j in range(1,df.shape[1]):
            if re.search('\D',df.iat[i,j]) is not None:
                print("value:" + str(df.iat[i,j]))
                raise NotNumericCharacterException
            if len(str(df.iat[i,j])) < 2 or len(str(df.iat[i,j])) > 3:
                raise InvalidNumericValueException
    df["Czas"] = df['Czas'].replace(";", ":", regex = True)


def clear_output_6psm(df_in, part_num):
    '''
    from the table recognized with PSM 6 we keep only the column with number of measurement
    and annotation column also cleans the result of invalid special characters
    :param df_in: original dataframe recognized with PSM 6
    :param partnum: number indicating if dataframe is left or right part of the table on page
    :return: cleaned and cropped dataframe
    '''
    df_test = df_in.copy()
    df_test = df_test.replace({'\(|\)|\||\{|\}|\[|\]': ''}, regex=True)
    #if there is no # sign in the column that means that the value was 1 values was readed as column name
    if re.search('#', df_test.columns[0]) is None:
        first_col = [df_test.columns[0]] + df_test.iloc[:, 0].dropna().tolist()
    else:
        first_col = df_test.iloc[:, 0].dropna().tolist()
    #if partnum == 0 then start the annotation column with R
    if part_num == 0:
        annon = ['R']
        i = 1
        final_col = [first_col[0]]
    else:
        annon = []
        i = 0
        final_col = []
    n = len(first_col)
    #if P is found amount values in first column then place it in annotation column in same row
    while i < n:
        if re.search('P|p|R', first_col[i]) is not None:
            annon.append('P')
            isempty = re.sub('\D', '', first_col[i])
            # if cell does not have any digit then delete it from first column
            if re.search('^\s*$', isempty) is None:
                final_col.append(isempty)
            else:
                final_col.append(first_col[i + 1])
                n -= 1
        else:
            annon.append(' ')
            final_col.append(first_col[i])
        i += 1
    return pd.DataFrame({'#': final_col, '_': annon})


def postprocess_dataframe(df1, df2, part_num):
    '''
    joins the result of both page segmentation methods after subtracting column from them
    :param df1:  dataframe recognized with PSM 11
    :param df2: dataframe recognized with PSM 6
    :param partnum: number indicating if dataframe is left or right part of the table on page
    :return: dataframe with replaced values
    '''
    df_right = clear_output_11psm(df1)
    df_left = clear_output_6psm(df2, part_num)
    concat = pd.concat([df_left, df_right], axis=1)
    return concat


def join_dataframes(df_list):
    '''
    joins the result from both left and right part of the table on page
    :param df_list: tuple with dataframes that is result of perdorm_clustering() method
    :return: dataframe with concatenated rows from two sides of the table
    '''
    part1 = postprocess_dataframe(df_list[0], df_list[2], 0)
    part2 = postprocess_dataframe(df_list[1], df_list[3], 1)
    result = pd.concat([part1, part2], axis=0)
    if len(result.columns) != 8:
        raise DataFrameColNumberException()
    return result.reset_index(drop=True)


######Patient and exam data reading######


def get_patient_and_exam_info(string):
    '''
    reads patient data fram the image, looks for words in chosen levenshtein distance from original words that
    are before choosen fields
    :param string: string with the text from first page of the exam result
    :return: dictionary with recognized values
    '''
    s_arr = string.split()
    for i in range(len(s_arr)):
        if nltk.edit_distance(s_arr[i], 'Nazwa:') <= 2:
            name = re.split(',', s_arr[i + 1])
            continue
        if nltk.edit_distance(s_arr[i], 'Identyfikator: ') <= 5:
            try:
                id = re.search('\d{3}/\d{3}', s_arr[i + 1]).group()
            except AttributeError:
                raise InformationNotFoundException
            continue
        if nltk.edit_distance(s_arr[i], 'urodzenia:') <= 4:
            try:
                date = re.search('\d{4}-\d{2}-\d{2}', s_arr[i + 1]).group()
            except AttributeError:
                raise InformationNotFoundException
            continue
        if nltk.edit_distance(s_arr[i], 'Rozpoczecie') <= 4 and nltk.edit_distance(s_arr[i + 1], 'skanowania:') <= 5:
            try:
                scan_start = re.search('\d{4}-\d{2}-\d{2}', s_arr[i + 2]).group() + " " + re.search('\d{2}:\d{2}',
                                                                                                    s_arr[
                                                                                                        i + 3]).group()
            except AttributeError:
                raise InformationNotFoundException
            continue
        if nltk.edit_distance(s_arr[i], 'Zakonczenie') <= 4 and nltk.edit_distance(s_arr[i + 1], 'skanowania:') <= 5:
            try:
                scan_end = re.search('\d{4}-\d{2}-\d{2}', s_arr[i + 2]).group() + " " + re.search('\d{2}:\d{2}',
                                                                                                  s_arr[i + 3]).group()
            except AttributeError:
                raise InformationNotFoundException
            continue
    return {'first_name': name[1], 'last_name': name[0], 'patient_id': id, 'birthdate': date,
            'scan_start_time': scan_start, 'scan_end_time': scan_end}


def get_attributes(image):
    '''
    performs pre-processing of the image and reads patients and exam data
    :param image: image of first page of test result in form of numpy arrays
    :return: return value of get_patient_and_exam_info()
    '''
    image_array = np.array(image)
    resized = resizing(image_array)
    tresh = color_and_treshold(resized)
    raw_string = pytesseract.image_to_string(tresh)
    return get_patient_and_exam_info(raw_string)


def image_check(img0,img1):
    '''
     checking if both images are from the exams results
    :param img0: image with the first page of the test result
    :param img1: image with the second page of the test result
    '''
    img0_arr = np.array(img0)
    img1_arr = np.array(img1)
    resized0 = resizing(img0_arr)
    resized1 = resizing(img1_arr)
    tresh0 = color_and_treshold(resized0)
    tresh1 = color_and_treshold(resized1)
    text0 = pytesseract.image_to_string(tresh0)
    text1 = pytesseract.image_to_string(tresh1)
    s_arr0 = text0.split()
    s_arr1 = text1.split()
    cond = [False,False]
    for i in range(len(s_arr0)):
         if nltk.edit_distance(s_arr0[i],'Informacje') <= 3 and nltk.edit_distance(s_arr0[i+1],'o') <= 1 and  nltk.edit_distance(s_arr0[i+2],'pacjencie') <= 3:
             cond[0] = True
    for i in range(len(s_arr1)):
        if nltk.edit_distance(s_arr1[i], 'ZESTAWIENIE') <= 4 and \
                nltk.edit_distance(s_arr1[i + 1], 'DANYCH') <= 2 and nltk.edit_distance(s_arr1[i + 2], 'SUROWYCH') <= 3:
            cond[1] = True
    if not (cond[0] and cond[1]):
        raise ExamNotFoundException()
