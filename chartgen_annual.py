import pandas as pd
import logtools_common.logtools_common as common
import os
from datetime import date

seperator = "-" * 125 + "\n"

def run():
    for yr in range(2018, date.today().year + 1):

        sql = "SELECT artist.artistname as Artist, count(log.logid) as Plays, sum(albumlengths.albumlength) as Time, Totals.TotalPlays, Totals.TotalTime "
        sql += "FROM log INNER JOIN albumartist ON log.albumid = albumartist.albumid "
        sql += "INNER JOIN albumlengths on albumartist.albumid = albumlengths.albumid "
        sql += "INNER JOIN album on albumlengths.albumid = album.albumid "
        sql += "INNER JOIN artist on albumartist.artistid = artist.artistid "
        sql += "JOIN (SELECT YEAR(log.logdate) as Y, COUNT(log.logid) as TotalPlays, SUM(albumlengths.albumlength) as TotalTime FROM log inner join albumlengths on log.albumid = albumlengths.albumid group by year(log.logdate)) Totals "
        sql += "WHERE YEAR(log.logdate) = " + str(yr) + " and Totals.Y = " + str(
            yr) + " and album.albumtypeid <> 16 GROUP BY Artist;"

        chart = pd.read_sql(sql, common.conn)

        chart['TimeScore'] = chart['Time'] / chart['TotalTime'] * 100
        chart['FreqScore'] = chart['Plays'] / chart['TotalPlays'] * 100
        chart['WeightedScore'] = (chart['TimeScore'] * 0.5) + (chart['FreqScore'] * 0.5)

        chart.sort_values('WeightedScore', ascending=False, inplace=True)

        chart['Rank'] = chart['WeightedScore'].rank(ascending=False)

        chart_formatted = chart[['Rank', 'Artist', 'TimeScore', 'FreqScore', 'WeightedScore']][:100]
        chart_array = chart_formatted.values.tolist()
        base_filename = "Artist Chart (Total) - {}.txt".format(yr)
        with open(os.path.join(common.basedir, 'Yearly', base_filename), 'w') as outfile:
            header = "{:<5}{:<80}{:>10}{:>10}{:>10}\n".format("RANK", "", "TIME", "FREQ", "TOTAL")
            outfile.write(seperator + header + seperator)

            for a in chart_array:
                rank, artist, timescore, freqscore, weightedscore = a
                textline = "{:<5}{:<80}{:>10.2f}{:>10.2f}{:>10.2f}\n".format(int(rank),
                                                                             common.shorten_by_word(artist.upper(), 80),
                                                                             timescore, freqscore, weightedscore)
                outfile.write(textline)
                outfile.write(seperator)

if __name__ == '__main__':
    run()
