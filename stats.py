import acct
import glob
import pandas as pd
# import numpy as np

def get_all_dbs(v=True):
    databases = glob.glob('/home/robale5/becauseinterfaces.com/acct/db/*econ*.db')
    # databases = glob.glob('../acct_legacy/db/*')
    if v: print(databases)
    return databases

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

if __name__ == '__main__':
    main()

# [2022-Jun-09 06:01:48 AM] ['/home/robale5/becauseinterfaces.com/acct/econ.py', '-db', 'econ_2022-06-09.db', '-s', '11', '-p', '4', '--early', '-i', 'items03_no_wip.csv']