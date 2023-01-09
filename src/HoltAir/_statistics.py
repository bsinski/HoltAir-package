import pandas as pd
import numpy as np
import datetime
from ._exceptions import InsufficientObesrvationsException

class ExamStatistics:
    '''
    contains dataframes with calculated statistics from exam data for day, night, joined and dictionary with pb_load values
    :param basic_overall: dataframe with basic statistics for day and night
    :param basic_day: dataframe with statistics for a  day
    :param basic_night: dataframe with statistics for a night
    :param bp_loadL dictionary with pb_load values for day, night and joined
    '''

    def __init__(self,df):
        self.basic_overall = join_overall_statistics(df)
        self.basic_day = get_statistics(df,'day')
        self.basic_night = get_statistics(df,'night')
        self.bp_load = bp_load_dictionary(df)


def get_statistics(dataframe, period):
    '''
        calculates basic statistics such sa mean,std,min and max for different blood pressure indicators
        :param dataframe: dataframe with blood pressure measurements
        :param period: parameter for choosing if statistics should be calculated for day, night or both
        :return: dataframe with calculated basic statistics
        '''
    df = dataframe.copy()
    df['Czas'] = transform_to_time(df['Czas'])
    df_statistics = pd.DataFrame(columns=['Measure', 'Mean', 'STD', 'Min', 'Max'])
    analysis_objects = [item for item in df.columns if item not in ['#', '_', 'Czas', 'Sleep']]
    if period == 'night':
        df = df[df['Sleep'] == 1]
    elif period == 'day':
        df = df[df['Sleep'] == 0]
    if df.shape[0] == 0:
        raise InsufficientObesrvationsException
    for measures in analysis_objects:
        analysis_col = df[measures].astype('int').tolist()
        newrow = [measures, np.mean(analysis_col), np.std(analysis_col), np.min(analysis_col), np.max(analysis_col)]
        df_statistics = pd.concat([df_statistics,pd.DataFrame([newrow], columns=['Measure', 'Mean', 'STD', 'Min', 'Max'])],
                                       ignore_index=True,axis=0)
    return df_statistics


def get_drop(dataframe):
    '''
    adds a column with the value of night time pressure drop for a data frame with both day and night.
    we do not calculate values for pulse pressure and heart rate
    :param dataframe: dataframe with blood pressure measurements for both day and night values
    :return: dataframe column with blood pressure drop
    '''
    df = dataframe.copy()
    df_day = get_statistics(dataframe,'day')
    df_night = get_statistics(dataframe,'night')
    drop = []
    for measure in ['Sys','Dia','SCT']:
        drop_value = 1 - float(df_night[df_night['Measure']==measure]['Mean']) / float(df_day[df_day['Measure']==measure]['Mean'])
        drop.append(drop_value)
    for i in range(len(df_day)-3):
        drop.append(np.nan)
    df_drop = pd.DataFrame({"Drop":drop})
    return df_drop


def get_morning_surge(dataframe):
    '''
    calculating the morning surge as the difference between the average pressure over a four-hour period before
    waking up and the average pressure over a period of four hours after waking up
    :param dataframe: dataframe with blood pressure measurements for both day and night values
    :return: column with morning surge values
    '''
    df = dataframe.copy()
    df['Czas'] = transform_to_time(df['Czas'])
    wakeup_time = df[df['Sleep']==0]['Czas'].min().to_pydatetime()
    moring_range = (wakeup_time - datetime.timedelta(hours=4),wakeup_time + datetime.timedelta(hours=4))
    surge = []
    for measure in ['Sys','Dia','SCT']:
        surge_value = np.mean(df[(df['Czas'] >= wakeup_time) & (df['Czas'] <= moring_range[1])][measure].astype('int')) - np.mean(df[(df['Czas'] <= wakeup_time )& (df['Czas'] >= moring_range[0])][measure].astype('int'))
        surge.append(surge_value)
    for i in range(2):
        surge.append(np.nan)
    df_surge =  pd.DataFrame({"Morning surge":surge})
    return df_surge


def join_overall_statistics(dataframe):
    '''
    joins dataframes with basic statistics for day and night and appends columsn with morning surge and drop values
    :param dataframe: dataframe with blood pressure measurements for both day and night values
    :return: concated dataframe
    '''
    df_statistics = get_statistics(dataframe,'all')
    df_drop = get_drop(dataframe)
    df_surge = get_morning_surge(dataframe)
    return pd.concat([df_statistics,df_drop,df_surge],axis=1)


def bp_load_dictionary(dataframe):
    '''
    calculates  the pb load value, which is the percentage of measurements above certain threshold values
    :param dataframe: dataframe with blood pressure measurements for both day and night values
    :return: dictionary with bp load values for night, day and both
    '''
    df = dataframe.copy()
    n = len(df)
    bp_all = len(df[(df['Sys'].astype('int') >= 130) | (df['Dia'].astype('int') >= 80)])/n
    df_day = df[df['Sleep']==0]
    bp_day = len(df_day[(df_day['Sys'].astype('int') >= 135) | (df_day['Dia'].astype('int') >= 85)])/n
    df_night = df[df['Sleep']==1]
    bp_night = len(df_night[(df_night['Sys'].astype('int') >= 120) | (df_night['Dia'].astype('int') >= 70)])/n
    return {"24hours":bp_all,"day":bp_day,"night":bp_night}


def transform_to_time(column):
    '''
    takes the time column and adds the 01-01-1900 date and creates datetime column, next it adds one day to the
    observations that are after 24:00.
    :param column: column with time of the blood pressure measurement
    :return: list with datetime observations
    '''
    list_with_time = pd.to_datetime(column,format='%H:%M').tolist()
    days_to_add = datetime.timedelta(days=0)
    for i in range(len(list_with_time)):
        if list_with_time[i] < list_with_time[i-1]:
            days_to_add = datetime.timedelta(days=1)
        newtime = list_with_time[i] + days_to_add
        list_with_time[i] = newtime.to_pydatetime()
    return list_with_time