import pandas as pd
import logtools_common.logtools_common as common
import matplotlib as plt
import os

from datetime import date, timedelta

seperator = "-" * 125 + "\n"

def get_last_rank(artistid, chart_date):
    last_week = chart_date - timedelta(days=7)
    results = common.get_results("SELECT rank FROM chart_history_rolling "
                                 "WHERE artistid={} and chartdate='{}';".format(artistid, last_week.strftime("%Y-%m-%d")))

    if results is None or len(results) == 0:
        return None
    else:
        return results[0][0]


def get_last_run(artistid):
    results = common.get_results("SELECT MAX(chartrun) FROM chart_history_rolling WHERE artistid={};".format(artistid))
    if results[0][0] is None:
        return 0
    else:
        return results[0][0]


def generate(chart_date=None):

    if chart_date is None:
        last_sunday = date.today() - timedelta(days=date.today().weekday() + 1)
    else:
        last_sunday = chart_date - timedelta(days=chart_date.weekday() + 1)

    date_range = last_sunday - timedelta(weeks=13) + timedelta(days=1)

    sql = "SELECT artist.artistid, artist.artistname as Artist, count(log.logid) as Plays, sum(albumlengths.albumlength) as Time, Totals.TotalPlays, Totals.TotalTime "
    sql += "FROM log INNER JOIN albumartist ON log.albumid = albumartist.albumid "
    sql += "INNER JOIN albumlengths on albumartist.albumid = albumlengths.albumid "
    sql += "INNER JOIN albumview as album on albumlengths.albumid = album.albumid "
    sql += "INNER JOIN artist on albumartist.artistid = artist.artistid "
    sql += "JOIN (SELECT COUNT(log.logid) as TotalPlays, SUM(albumlengths.albumlength) as TotalTime FROM log inner join albumlengths on log.albumid = albumlengths.albumid) Totals "
    sql += "WHERE log.logdate BETWEEN '{}' AND '{}' and album.albumtypeid <> 16 GROUP BY Artist;".format(
        date_range.strftime("%Y-%m-%d"), last_sunday.strftime("%Y-%m-%d"))

    chart = pd.read_sql(sql, common.conn)

    chart['TimeScore'] = (chart['Time'] / chart['TotalTime']) * 100
    chart['FreqScore'] = (chart['Plays'] / chart['TotalPlays']) * 100
    chart['WeightedScore'] = (chart['TimeScore'] * 0.5) + (chart['FreqScore'] * 0.5)

    chart.sort_values('WeightedScore', ascending=False, inplace=True)

    chart['Rank'] = chart['WeightedScore'].rank(ascending=False)

    chart_formatted = chart[['Rank', 'artistid', 'Artist', 'TimeScore', 'FreqScore', 'WeightedScore']][:40]

    chart_array = chart_formatted.values.tolist()
    base_filename = "Artist Chart (Rolling) - {}.txt".format(last_sunday.strftime("%Y-%m-%d"))
    full_dir = os.path.join(common.basedir, 'Rolling', 'Artist')

    common.execute_sql("DELETE FROM chart_history_rolling WHERE chartdate='{}' AND artistid <> 0;".format(last_sunday.strftime("%Y-%m-%d")))

    if not os.path.exists(full_dir):
        os.makedirs(full_dir)

    with open(os.path.join(full_dir, base_filename), 'w', encoding='utf-8') as outfile:
        header = "{:<5}{:<5}{:<80}{:>10}{:>10}{:>10}\n".format("RANK", "+/-", "", "TIME", "FREQ", "TOTAL")
        outfile.write(seperator + header + seperator)

        for a in chart_array:
            rank, artistid, artist, timescore, freqscore, weightedscore = a
            lw_rank = get_last_rank(artistid, last_sunday)
            lw_string=""

            chartrun = get_last_run(artistid)
            if lw_rank is None:
                if chartrun == 0:
                    lw_string = "N"
                    chartrun = 1
                else:
                    lw_string = "R"
                    chartrun += 1
            else:
                if int(rank) < lw_rank:
                    lw_string = "+"
                else:
                    lw_string = ""

            textline = "{:<5}{:<5}{:<80}{:>10.2f}{:>10.2f}{:>10.2f}\n".format(int(rank), lw_string,
                                                                         common.shorten_by_word(artist.upper(), 80),
                                                                         timescore, freqscore, weightedscore)


            common.add_rolling_chart_history(last_sunday.strftime("%Y-%m-%d"), artistid, 0, rank, weightedscore, chartrun)
            outfile.write(textline)
            outfile.write(seperator)

def run():
    common.execute_sql("DELETE FROM chart_history_rolling where artistid <> 0;")
    start_date = date(2018,4,9)
    while start_date < date.today():
        generate(start_date)
        start_date += timedelta(days=7)

if __name__ == '__main__':
    run()