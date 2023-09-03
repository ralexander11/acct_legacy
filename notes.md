
1. [Done] Get Godot installed and working.
2. [Done] Get basic tutorial game complete and working.
3. [Done] Watch Tile map tutorial.
4. [Done] Chop FF6 map up into files in graphic program.
5. [Done] Make tile map with FF6 tiles.
6. [Done] Make actor character that can move around tiles.
7. [Done] Add collision system for specific tiles.

8. Convert movement into turn based system.
9. Add an enemy.
10. Add attack ability.
11. Add ability for enemy to move around a bit.

# Download market data locally
00 20 * * * rsync -a --ignore-existing robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/market_data/data /home/robbie/dev/acct_legacy/market_data

# Save down websites
rsync -a robale5@becauseinterfaces.com:/home/robale5 /home/robbie/dev/website

# Other stuff
python -u combine_data.py -t vfv-ct -sd 2023-05-02 -o vfv-ct_merged_test02.csv -s -v

scp merged_2020-01-24_to_2021-04-30.csv robale5@becauseinterfaces.com:/home/robale5/becauseinterfaces.com/acct/market_data/data

python market_data/combine_data.py -sd 2020-01-24 -ed 2021-04-30 -o merged_2020-01-24_to_2021-04-30.csv -s -v

python market_data/combine_data.py -md merged_2023-02-28_to_2023-07-22.csv -o merged_2023-02-28_to_2023-07-22_splits.csv -m splits -s -v

python market_data/combine_data.py -md merged_2023-02-28_to_2023-07-22_splits.csv -o merged_2023-02-28_to_2023-07-22_mark.csv -m mark -s -v

# splits, mark, scrub, tar

nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/fut_price.py --seed 11 -n -t vfv-ct -d merged_2023-02-28_to_2023-07-22.csv -o vfv-recent01 -s >> /home/robale5/becauseinterfaces.com/acct/logs/fut_price_vfv01.log 2>&1 &

nohup python -u fut_price.py --seed 11 -n -t vfv-ct -d merged_2023-02-28_to_2023-07-22.csv -o vfv-recent01 -s >> logs/fut_price_vfv01.log 2>&1 &

#crontab

# Get market data
00 18 * * * nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/market_data/market_data.py >> /home/robale5/becauseinterfaces.com/acct/logs/market_data.log 2>&1 &
#
# Run trade algo
00 22 * * * nohup /home/robale5/venv/bin/python -u /home/robale5/becauseinterfaces.com/acct/trade_algo.py -db vfv01.db -t vfv-ct --model_name "vfv-past01, vfv-recent01" >> /home/robale5/becauseinterfaces.com/acct/logs/vfv01.log 2>&1 &

# Get market data locally
00 22 * * * /home/robbie/anaconda3/bin/python -u /home/robbie/dev/acct_legacy/market_data/market_data.py >> /home/robbie/dev/acct_legacy/logs/market_data.log 2>&1

# Run locally
python market_data/combine_data.py -sd 2023-03-24 -ed 2023-03-30 -o merged_test.csv -s -v
# Run locally
nohup python -u trade_algo.py -db vfv01.db -t vfv-ct --model_name "vfv-past01, vfv-recent01" -r >> logs/vfv01.log 2>&1 &