1. The files shared_functions.py and historical_analysis.py are just there to calculate the percentile tables of NBM. They are not using live data.
2. The file live_monitor.py takes the live prices and then calculates the dip and then matches them with the tables we have. This way we don't disturb the other two files by live data.
   We just them to compare our live data to the historical percentiles.

 