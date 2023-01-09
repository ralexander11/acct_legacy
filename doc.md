# Finance Trading Documentation and Workflows

## Getting the Data
Use the combine_data.py script in the market_data dir.
The mode can be set with the -m argument. Use -h argument to see all the modes.
    To get the latest data for models use -m get.
Use the -d argument to choose the dates.
    Can leave blank for all dates available.
    It can be one or more dates separated by comas.
    # TODO But if '.csv' is in the argument, it will try to load the file.
Use the -t argument to choose the tickers.
    It can be one or more tickers separated by comas.
    # TODO Or can provide keywords.
    # TODO But if '.csv' is in the argument, it will try to load the file.
Use the -out argument to specify the output filename with no .csv extension.

