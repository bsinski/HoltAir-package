import datetime
import numpy as np


def find_lows(values, times, lag=4, threshold=1, influence=0):
    '''
    finds low fragments of a signal
    https://stackoverflow.com/questions/22583391/peak-signal-detection-in-realtime-timeseries-data/22640362#22640362

    return: array consisting of 1s and 0s where 1 indicate low areas
    '''


    signals = np.zeros(len(values))
    filtered_y = np.array(values)
    avg_filter = [0] * len(values)
    std_filter = [0] * len(values)
    avg_filter[lag - 1] = np.mean(values[0:lag])
    std_filter[lag - 1] = np.std(values[0:lag])
    for i in range(lag, len(values)):
        if abs(values[i] - avg_filter[i - 1]) > threshold * std_filter[i - 1] and times[i].hour not in range(11, 21):
            if values[i] > avg_filter[i - 1]:
                signals[i] = 0
            else:
                signals[i] = 1

            filtered_y[i] = influence * values[i] + (1 - influence) * filtered_y[i - 1]
            avg_filter[i] = np.mean(filtered_y[(i - lag + 1):i + 1])
            std_filter[i] = np.std(filtered_y[(i - lag + 1):i + 1])
        else:
            signals[i] = 0
            filtered_y[i] = values[i]
            avg_filter[i] = np.mean(filtered_y[(i - lag + 1):i + 1])
            std_filter[i] = np.std(filtered_y[(i - lag + 1):i + 1])

    return signals


def find_longest_sleep(array):
    '''
    finds longest subarray of 1s (indicating sleep)
    :param array: array consisting of 0s and 1s where 1 indicate sleep
    :return: start and end index of longest sleep
    '''
    max_count = 0
    start_index = 0
    max_start_index = 0
    max_end_index = 0
    count = 0

    for i, e in enumerate(array):
        if e == 1:
            count += 1
        if e == 0:
            if count > max_count:
                max_count = count
                max_start_index = start_index
                max_end_index = i - 1
            count = 0
            start_index = i
    return max_start_index, max_end_index


def fill_sleep(arr):
    '''
    fills gaps in sleep array - sometimes there's some sort of one-time activity during the sleep phase,
    which disrupts results Example: subarray (1,1,0,1) becomes (1,1,1,1)
    :param arr: array of 1s and 0s indicating sleep
    :return: new array with filled gaps
    '''
    new_arr = [0] * len(arr)
    for i in range(2, len(arr) - 2):
        if (arr[i-2], arr[i - 1], arr[i], arr[i + 1]) == (1, 1, 0, 1):
            new_arr[i] = 1
        else:
            new_arr[i] = arr[i]
    return new_arr


def detect_sleep(results_df, colname="merged", lag=5, threshold=1.15, influence=0):
    '''

    :param results_df: dataframe (probably from Exam object) containg measurement results
    :param colname: column on which sleep will be detected. Default: 'Sys', if no results - 'Dia' is tried
    :return: array containing 1s and 0s where 1s indicate sleep. If viable sleep is detected, it defaults to 22:00-6:00
    '''
    results_df["merged"]= (results_df["Sys"]+results_df["Dia"]+results_df['SCT'])/3   

    casted_col = np.array(results_df[colname].astype(None))

    # time column as datetime.datetime, if before 1 pm - replace date
    times = results_df["Czas"].apply(lambda x: datetime.datetime(1990, 1, 1, int(x.split(":")[0]), int(x.split(":")[1])))
    for i, x in enumerate(times):
                        if x.hour<13:
                            times[i] = times[i].replace(day=2)
    
    sleep = find_lows(casted_col, times, lag, threshold, influence)
    #sleep = [x if times[i].hour not in range(11, 21) else 0 for i, x in enumerate(sleep)]
    sleep = fill_sleep(sleep)

    start, end = find_longest_sleep(sleep)

    length = ((times[end] - times[start]).seconds)/3600 #in hours

    results_df.drop(columns=['merged'], inplace=True)

    # we want sleep  [5,10] hours long and not ending before 3 am
    if length >= 5 and length <= 10 and times[end].hour > 3:
        return [x if i in range(start, end + 1) else 0 for i, x in enumerate(sleep)], "detected"
    else:
        return [1 if times[i].hour not in range(6, 22) else 0 for i in range(len(times))], "default"
