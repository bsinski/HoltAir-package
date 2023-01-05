import pandas as pd
import numpy as np
import datetime
from .utils import transform_to_time
from .exceptions import InsufficientObesrvationsException

class ExamStatistics:
    def __init__(self,df):
        self.basic_overall = join_overall_statistics(df)
        self.basic_day = get_statistics(df,'day')
        self.basic_night = get_statistics(df,'night')
        self.bp_load = bp_load_dictionary(df)

# wyliczanie podstawowych statystyk o wybranej porze dnia
def get_statistics(dataframe, period):
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
        df_statistics = df_statistics.append(pd.DataFrame([newrow], columns=['Measure', 'Mean', 'STD', 'Min', 'Max']),
                                       ignore_index=True)
    return df_statistics


# dodanie kolumny z wartością nocnego spadku ciśnienia dla ramki danych z zarówno dniem i nocą
# nie wyliczamy wartości dla ciśnienia tętna i częstości pracy serca
def get_drop(dataframe):
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


# wyliczanie porannego spadku ciśnienia jako różnica pomiędzy średnim ciśnieniem w okresie czterech godzin przed pobódką,
# a średnim cisnieniem w okresie czterech godzin po przebudzeniu
def get_morning_surge(dataframe):
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

# łączenie wynikowych ramek danych
def join_overall_statistics(dataframe):
    df_statistics = get_statistics(dataframe,'all')
    df_drop = get_drop(dataframe)
    df_surge = get_morning_surge(dataframe)
    return pd.concat([df_statistics,df_drop,df_surge],axis=1)

# wyliczanie wartości pb load, która jestodsetkiem pomiarów powyżej określonych wartości progowych
def bp_load_dictionary(dataframe):
    df = dataframe.copy()
    n = len(df)
    bp_all = len(df[(df['Sys'].astype('int') >= 130) | (df['Dia'].astype('int') >= 80)])/n
    df_day = df[df['Sleep']==0]
    bp_day = len(df_day[(df_day['Sys'].astype('int') >= 135) | (df_day['Dia'].astype('int') >= 85)])/n
    df_night = df[df['Sleep']==1]
    bp_night = len(df_night[(df_night['Sys'].astype('int') >= 120) | (df_night['Dia'].astype('int') >= 70)])/n
    return {"24hours":bp_all,"day":bp_day,"night":bp_night}
