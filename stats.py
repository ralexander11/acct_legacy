import acct
import glob
import pandas as pd
# import numpy as np
import re

def get_all_dbs(v=True):
    databases = glob.glob('/home/robale5/becauseinterfaces.com/acct/db/*econ*.db')
    # databases = glob.glob('../acct_legacy/db/*econ*')
    if v: print(databases)
    return databases

def get_all_logs(v=True):
    # logs = glob.glob('/home/robale5/becauseinterfaces.com/acct/logs/*econ*.log')
    logs = glob.glob('../acct_legacy/logs/*econ*')
    if v: print(logs)
    return logs

def main_logs(v=True):
    timings = []
    cols = ['db_file', 'date', '2: Corp (min)', '3: Entity check (min)', '5: Optional check (min)', '6: Prices check (sec)', '7: Needs decay (min)', '8: Cash check (sec)', '9: Birth check (min)', '4: Demand check (min)', '4.1: Demand auto (sec)', '4.2: ', '4.3: ', '4.4: ', '4.5: ', '4.6: ', '4.7: ', '4.8: ', '4.9: ', '1: End (min)']
    logs = get_all_logs()
    num_logs = len(logs)
    print('num_logs:', num_logs)
    logs.sort()
    first = True
    for i, log in enumerate(logs):
        print(f'{i+1}/{num_logs} log:', log)
        log_name, date, match_time2, match_time3, match_time5, match_time6, match_time7, match_time8, match_time9, match_time4, match_time4_1, match_time4_2, match_time4_3, match_time4_4, match_time4_5, match_time4_6, match_time4_7, match_time4_8, match_time4_9, match_time1 = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
        log_name = log.split('/')[-1]
        # try:
        with open(log) as f:
            for line in f:
                date_match = re.search(r'Current Date 01:\s\d{4}-\d{2}-\d{2}', line)
                if date_match:
                    date_match2 = re.search(r'\d{4}-\d{2}-\d{2}', date_match.group())
                    if date_match2:
                        if not first:
                            timings.append([log_name, date, match_time2, match_time3, match_time5, match_time6, match_time7, match_time8, match_time9, match_time4, match_time4_1, match_time4_2, match_time4_3, match_time4_4, match_time4_5, match_time4_6, match_time4_7, match_time4_8, match_time4_9, match_time1])
                        first = False
                        date = date_match2.group()
                    
                match2 = re.search(r'\s2:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match2:
                    match_time2 = re.search(r'\d+\.\d\d', match2.group())
                    if match_time2:
                        match_time2 = match_time2.group()
                        print(match_time2)

                match3 = re.search(r'\s3:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match3:
                    match_time3 = re.search(r'\d+\.\d\d', match3.group())
                    if match_time3:
                        match_time3 = match_time3.group()
                        print(match_time3)
                
                match5 = re.search(r'\s5:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match5:
                    match_time5 = re.search(r'\d+\.\d\d', match5.group())
                    if match_time5:
                        match_time5 = match_time5.group()
                        print(match_time5)
                
                match6 = re.search(r'\s6:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match6:
                    match_time6 = re.search(r'\d+\.\d\d', match6.group())
                    if match_time6:
                        match_time6 = match_time6.group()
                        print(match_time6)
                
                match7 = re.search(r'\s7:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match7:
                    match_time7 = re.search(r'\d+\.\d\d', match7.group())
                    if match_time7:
                        match_time7 = match_time7.group()
                        print(match_time7)
                
                match8 = re.search(r'\s8:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match8:
                    match_time8 = re.search(r'\d+\.\d\d', match8.group())
                    if match_time8:
                        match_time8 = match_time8.group()
                        print(match_time8)
                
                match9 = re.search(r'\s9:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match9:
                    match_time9 = re.search(r'\d+\.\d\d', match9.group())
                    if match_time9:
                        match_time9 = match_time9.group()
                        print(match_time9)
                
                match4 = re.search(r'\s4:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4:
                    match_time4 = re.search(r'\d+\.\d\d', match4.group())
                    if match_time4:
                        match_time4 = match_time4.group()
                        print(match_time4)
                
                match4_1 = re.search(r'\s4\.1:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4_1:
                    match_time4_1 = re.search(r'\d+\.\d\d', match4_1.group())
                    if match_time4_1:
                        match_time4_1 = match_time4_1.group()
                        print(match_time4_1)
                
                match4_2 = re.search(r'\s4\.1:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4_2:
                    match_time4_2 = re.search(r'\d+\.\d\d', match4_2.group())
                    if match_time4_2:
                        match_time4_2 = match_time4_2.group()
                        print(match_time4_2)
                
                match4_3 = re.search(r'\s4\.1:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4_3:
                    match_time4_3 = re.search(r'\d+\.\d\d', match4_3.group())
                    if match_time4_3:
                        match_time4_3 = match_time4_3.group()
                        print(match_time4_3)
                
                match4_4 = re.search(r'\s4\.1:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4_4:
                    match_time4_4 = re.search(r'\d+\.\d\d', match4_4.group())
                    if match_time4_4:
                        match_time4_4 = match_time4_4.group()
                        print(match_time4_4)
                
                match4_5 = re.search(r'\s4\.1:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4_5:
                    match_time4_5 = re.search(r'\d+\.\d\d', match4_5.group())
                    if match_time4_5:
                        match_time4_5 = match_time4_5.group()
                        print(match_time4_5)
                
                match4_6 = re.search(r'\s4\.1:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4_6:
                    match_time4_6 = re.search(r'\d+\.\d\d', match4_6.group())
                    if match_time4_6:
                        match_time4_6 = match_time4_6.group()
                        print(match_time4_6)
                
                match4_7 = re.search(r'\s4\.1:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4_7:
                    match_time4_7 = re.search(r'\d+\.\d\d', match4_7.group())
                    if match_time4_7:
                        match_time4_7 = match_time4_7.group()
                        print(match_time4_7)
                
                match4_8 = re.search(r'\s4\.1:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4_8:
                    match_time4_8 = re.search(r'\d+\.\d\d', match4_8.group())
                    if match_time4_8:
                        match_time4_8 = match_time4_8.group()
                        print(match_time4_8)
                
                match4_9 = re.search(r'\s4\.1:.+took\s\d+\.\d\d\s(sec|min)', line)
                if match4_9:
                    match_time4_9 = re.search(r'\d+\.\d\d', match4_9.group())
                    if match_time4_9:
                        match_time4_9 = match_time4_9.group()
                        print(match_time4_9)

                match1 = re.search(r'End of Econ Update for.+took\s\d+\.\d\d\s(sec|min)', line)
                if match1:
                    match_time1 = re.search(r'\d+\.\d\d', match1.group())
                    if match_time1:
                        match_time1 = match_time1.group()
                        print(match_time1)

        # except Exception as e:
        #     print(f'Error with file: {log}')
        #     print(e)
        #     print('------------------------------------------')
        #     continue

    df = pd.DataFrame(timings, columns=cols)
    print(df)
    df.to_csv('data/timings.csv', index=True)
    return df

def main(v=True):
    stats = []
    dbs = get_all_dbs()
    num_dbs = len(dbs)
    print('num_dbs:', num_dbs)
    dbs.sort()
    for i, db in enumerate(dbs):
        print(f'{i+1}/{num_dbs} db:', db)
        db = db.split('/')[-1]
        if v: print('db file:', db)
        try:
            accts = acct.Accounts(conn=db)
            ledger = acct.Ledger(accts)

            txns = ledger.get_gl_count()
            dur = ledger.duration()
            days = ledger.count_days()
            date = ledger.latest_date()
            item = ledger.latest_item()
        except Exception as e:
            print(f'Error with file: {db}')
            print(e)
            print('------------------------------------------')
            continue
        if dur.days == 0:
            txn_eff = txns // 1
            day_eff = days // 1
        else:
            txn_eff = txns // dur.days
            day_eff = days // dur.days

        stats.append([db, date, item, txns, days, dur, txn_eff, day_eff.days])

        # print('txns:', txns)
        # print('dur:', dur)
        # print('days:', days)
        if v: print('txn per day:', txn_eff)
        if v: print('days per real day:', day_eff)
        if v: print('------------------------------------------')
        cols = ['db_file', 'date', 'item', 'txns', 'days', 'dur', 'txn_eff', 'day_eff']
    # print(dbs)
    # print('----------------------------------------')
    df = pd.DataFrame(stats, columns=cols)
    print(df)
    df.to_csv('data/stats.csv', index=True)
    return df

def gl_timings():

    return

if __name__ == '__main__':
    # main()
    main_logs()
    # gl_timings()

# [2022-Jun-09 06:01:48 AM] ['/home/robale5/becauseinterfaces.com/acct/econ.py', '-db', 'econ_2022-06-09.db', '-s', '11', '-p', '4', '--early', '-i', 'items03_no_wip.csv']