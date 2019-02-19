import pandas as pd
import logtools_common.logtools_common as common
import os
from datetime import date

seperator = "-" * 125 + "\n"

def run():
    for source in ['Vinyl','CD','Cassette','Digital']:
        sql = "SELECT album.artistcredit as Artist, albumlengths.album as Album, source.source, count(log.logid) as Plays, sum(albumlengths.albumlength) as Time, Totals.TotalPlays, Totals.TotalTime "
        sql += "FROM log INNER JOIN albumlengths on log.albumid = albumlengths.albumid "
        sql += "INNER JOIN album on albumlengths.albumid = album.albumid " \
               "INNER JOIN source on album.sourceid = source.sourceid "
        sql += "JOIN (SELECT COUNT(log.logid) as TotalPlays, SUM(albumlengths.albumlength) as TotalTime FROM log inner join albumlengths on log.albumid = albumlengths.albumid) Totals "
        sql += "WHERE album.albumtypeid <> 16 and log.logdate >= '2017-01-01' and source = '{}' GROUP BY Artist, Album, source;".format(source)

        chart = pd.read_sql(sql, common.conn)

        chart['TimeScore'] = (chart['Time'] / chart['TotalTime']) * 100
        chart['FreqScore'] = (chart['Plays'] / chart['TotalPlays']) * 100
        chart['WeightedScore'] = ((chart['TimeScore'] * 0.5) + (chart['FreqScore'] * 0.5))

        chart.sort_values('WeightedScore', ascending=False, inplace=True)

        chart['Rank'] = chart['WeightedScore'].rank(ascending=False)

        chart_formatted = chart[['Rank', 'Artist', 'Album', 'TimeScore', 'FreqScore', 'WeightedScore']][:25]
        chart_array = chart_formatted.values.tolist()
        base_filename = "Album Chart - {}.txt".format(source)
        full_dir = os.path.join(common.basedir, 'By Format')
        if not os.path.exists(full_dir):
            os.makedirs(full_dir)
        with open(os.path.join(full_dir, base_filename), 'w', encoding='utf-8') as outfile:
            header = "{:<5}{:<80}{:>10}{:>10}{:>10}\n".format("RANK", "", "TIME", "FREQ", "TOTAL")
            outfile.write(seperator + header + seperator)

            for a in chart_array:
                rank, artist, album, timescore, freqscore, weightedscore = a
                textline = "{:<5}{:<80}{:>10.2f}{:>10.2f}{:>10.2f}\n".format(int(rank),
                                                                             common.shorten_by_word(artist.upper() + ": " + album, 80),
                                                                             timescore, freqscore, weightedscore)
                outfile.write(textline)
                outfile.write(seperator)

if __name__ == '__main__':
    run()
