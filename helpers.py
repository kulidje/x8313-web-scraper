# helper functions for core script

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import calendar
from pandas import read_csv
from config.configuration import load_configuration

c = load_configuration()

# initialize data dict: {'AJAX DOWNS TIPS': 'AJX', 'ALBUQUERQUE TIPS': 'ALB' ...}
dict_gts_track_symbols = read_csv('data/gts_track_symbols.csv').set_index('track_name')['track_symbol'].to_dict()


def make_canonical_horse_name(name):
    # rules:
    # 1) make all caps
    # 2) remove all parentheses and contents (foreign horses)
    # 3) remove all spaces and apostrophes
    canonical_name = name.upper().replace("'", "").strip()
    ending = canonical_name.find("(")
    if ending != -1:
        canonical_name = canonical_name[0:ending].strip().replace(" ", "")
    return canonical_name.replace(" ", "")


def get_track_symbol(text):
    # returns track symbol
    track_name = text[0: text.find('-')].strip()
    return dict_gts_track_symbols[track_name]


def get_date(text):
    # returns date as string
    year = str(text[-4:])
    day = str(text[-8:-6])

    # dict of {'JANUARY': '01' ... 'DECEMBER': '12'}
    dict_months = {str.upper(calendar.month_name[i]): str.zfill(str(i), 2) for i in range(1, 13)}

    for each_month in dict_months:
        if each_month in text:
            month = dict_months[each_month]

    return year + month + day
