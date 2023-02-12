# Finance Trading Documentation and Workflows

## Getting the Data
Use the *combine_data.py* script in the market_data dir.

-d argument to choose the dates.
    Can leave blank for all dates available.
    It can be one or more dates separated by comas.
    But if '.csv' is in the argument, it will try to load the file.

-t argument to choose the tickers.
    It can be one or more tickers separated by comas.
    # TODO Or can provide keywords.
    But if '.csv' is in the argument, it will try to load the file.

-f argument to choose the fields.
    Can leave blank to use all fields.
    It can be one or more fields separated by comas.
    But if '.csv' is in the arugment, it will try to load the file.

-o argument to specify the output filename with no .csv extension.
    If this is not used, the default file name is 'merged.csv'.

-s argument to save the output.

-m optional argument to set the mode:
    Don't use the argument to combine the data.
    merged, find, missing, tickers, value, crypto, splits, mark, scrub, tar, gettickers, maxdate, mindate, and get.
    -m get: to get data to run a model.

```nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/combine_data.py -m get -t "aapl, tsla" -s >> /home/robale5/becauseinterfaces.com/acct/logs/get14.log 2>&1 &```

## Create the Model
Use the *fut_price.py* script to create a new model.
    -t with a single ticker to run the model for that ticker.
    -n to train a new model.
    -seed the seed for the randomness of the training. I often use "11".
    -d the name of the input csv data file to use.
    -o the name to save the model as.
    -s to save the model.

```nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/fut_price.py -d merged_bak_2021-02-25.csv -n -t tsla --seed 11 -s >> /home/robale5/becauseinterfaces.com/acct/logs/fut_price09.log 2>&1 &```

## Use the Model
Use the *trade_algo.py* script to test and use the model.
    -db the database name to save the results in.
    -cap the amount of capital to start with.
    -sim to run the model on historical data.
    -mn a coma separated list of one or more model names.
    -d the name of the input csv data file to use, if needed.

```nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/trade_algo.py -db trade02.db -s 11 -t tsla -sim >> /home/robale5/becauseinterfaces.com/acct/logs/trade02.log 2>&1 &```