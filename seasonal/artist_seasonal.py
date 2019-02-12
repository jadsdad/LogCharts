import pandas as pd
import logtools_common.logtools_common as common
import os
from datetime import date

seperator = "-" * 125 + "\n"
seasons = {"Q1 - Winter": "1, 2, 3",
          "Q2 - Spring": "4, 5, 6",
          "Q3 - Summer": "7, 8, 9",
          "Q4 - Autumn": "10, 11, 12"}

def run():
    for yr in range(2018, date.today().year + 1):
        for season, monthstring in seasons.items():
            sql = "SELECT artist.artistname as Artist, count(log.logid) as Plays, sum(albumlengths.albumlength) as Time, Totals.TotalPlays as TotalPlays, Totals.TotalTime "
            sql += "FROM log INNER JOIN albumlengths on log.albumid = albumlengths.albumid "
            sql += "INNER JOIN albumartist on albumlengths.albumid = albumartist.albumid "
            sql += "INNER JOIN artist on artist.artistid = albumartist.artistid "
            sql += "INNER JOIN album on album.albumid = albumartist.albumid "
            sql += "JOIN (SELECT COUNT(log.logid) as TotalPlays, SUM(albumlengths.albumlength) as TotalTime FROM log inner join albumlengths on log.albumid = albumlengths.albumid) Totals "
            sql += "WHERE YEAR(log.logdate) = " + str(
                yr) + " and MONTH(log.logdate) IN (" + monthstring + ") and album.albumtypeid <> 16 GROUP BY Artist;"

            chart = pd.read_sql(sql, common.conn)

            chart['TimeScore'] = (chart['Time'] / chart['TotalTime']) * 100
            chart['FreqScore'] = (chart['Plays'] / chart['TotalPlays']) * 100
            chart['WeightedScore'] = (chart['TimeScore'] * 0.5) + (chart['FreqScore'] * 0.5)

            chart.sort_values('WeightedScore', ascending=False, inplace=True)

            chart['Rank'] = chart['WeightedScore'].rank(ascending=False)

            chart_formatted = chart[['Rank', 'Artist', 'TimeScore', 'FreqScore', 'WeightedScore']][:25]
            chart_array = chart_formatted.values.tolist()

            base_filename = "Artist Chart - {} {}.txt".format(yr, season)

            if len(chart_array) > 1:
                with open(os.path.join(common.basedir, 'Seasonal', 'Artist', base_filename),'w') as outfile:
                    header = "{:<5}{:<80}{:>10}{:>10}{:>10}\n".format("RANK","","TIME","FREQ","TOTAL")
                    outfile.write(seperator + header + seperator)

                    for a in chart_array:
                        rank, artist, timescore, freqscore, weightedscore = a
                        textline = "{:<5}{:<80}{:>10.2f}{:>10.2f}{:>10.2f}\n".format(int(rank), common.shorten_by_word(artist.upper(), 80), timescore, freqscore, weightedscore)
                        outfile.write(textline)
                        outfile.write(seperator)

if __name__ == '__main__':
    run()
