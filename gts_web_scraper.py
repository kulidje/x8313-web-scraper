import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
from helpers import *
import os

# time zone
TORONTO = datetime.datetime.utcnow() - datetime.timedelta(hours=4)
date = TORONTO.strftime('%Y%m%d')

if not os.path.exists(c['output']):
    os.makedirs(c['output'])

# request and get downloads page as response object
url = 'https://www.guaranteedtipsheet.com'
res = requests.get(url + '/download.asp')
res.raise_for_status()

# create soup object from download page, then create another soup object with all race tags on page selected
downloads_soup = BeautifulSoup(res.text, 'lxml')
downloads_tags = downloads_soup.select('table a')

# details to be used in login POST request
payload = {
    'txtusername': c['gts_username'],
    'txtpassword': c['gts_password'],
    'Submit': 'Submit'
}

headers_dict = {
    'origin': 'https://www.guaranteedtipsheet.com',
    'referer': 'https://www.guaranteedtipsheet.com/index.asp?login=1&err=1'
}

for tag in downloads_tags:

    # Use 'with' to ensure the session context is closed after use.
    with requests.Session() as s:
        p = s.post(url + '/checklogin.asp', data=payload, headers=headers_dict)

        # An authorised request.
        r = s.get('http://www.guaranteedtipsheet.com/' + tag['href'])

    try:
        # make list of pandas df from html (in this case, list contains only 1 element)
        df_list = pd.read_html(r.text, attrs={'id': 'table1'}, converters={2: lambda x: x.replace('*', '').strip()})

    except Exception as e:
        continue

    df = df_list[0]  # instantiate df

    # get date and symbol and check if track is flagged
    symbol = get_track_symbol(df[0][1])
    date = get_date(df[0][1])
    if symbol in ['LAQ', 'LRC', '???', 'M']:
        continue

    # upload raw data to factors.db
    df.to_csv(os.path.join(c['output'], 'gts_raw_%s.csv' % date), index=False, dtype=str)

    # add 'sentinel_RACE' column to df to act as race_num indicator for parsing mechanism
    df['sentinel_RACE'] = df[0].map(lambda x: int(str(x).startswith('RACE'))).cumsum()

    factor_value_dict = {'WIN': 'Win', 'PLACE': 'Place', 'SHOW': 'Show', 'WILD CARD': 'WC',
                         'ALTERNATE 1': 'A1', 'ALTERNATE 2': 'A2'}

    # transform df where Columns have values
    df = df.loc[df[0].isin(list(factor_value_dict.keys()))]
    df = df.reset_index(drop=True)

    df.dropna(inplace=True)  # delete rows with Nan values
    if len(df) == 0:
        continue

    # add runner_id column
    df['runner_id'] = df.loc[:, [2, 'sentinel_RACE']].map(lambda x: symbol + '_' + date + '_{}_{}'.format(x[1], x[0]), axis=1)

    # final clean up
    df[0] = df[0].map(lambda x: factor_value_dict[x])  # WIN to Win, ALTERNATE 1 to A1 etc. w/ dict
    df[3] = df[3].map(make_canonical_horse_name)
    df = df.drop([1, 2, 'sentinel_RACE'], 1)  # drop columns
    df['factor_name'] = 'FACTOR_CATEGORICAL_RUNNER_GTS'  # fill factor_name column
    df['timestamp'] = str(TORONTO)  # timestamp column
    df['date'] = df['runner_id'].map(lambda x: x.split('_')[1])  # date column - date of race as str
    df['race_id'] = df['runner_id'].map(lambda x: x[:x.rfind('_')])  # race_id column
    df = df.reindex_axis(['timestamp', 'race_id', 'date', 'runner_id', 3, 'factor_name', 0], axis=1)  # change order of columns
    df.columns = ['timestamp', 'race_id', 'date', 'runner_id', 'x8name', 'factor_name', 'factor_value']  # rename columns

    # upload transformed df to factors.db
    df.to_csv(os.path.join(c['output'], 'gts_processed_%s.csv' % date), index=False)
