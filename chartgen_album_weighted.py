from pathlib import Path
import os
import io
from datetime import date
import logtools_common.logtools_common as common

basedir = str(Path.home()) + "/Charts"
conn = common.conn
seperator = "-" * 125 + "\n"
totalplays = 0
totaltime = 0


def get_total_plays(y):
    if y > 0:
        sql = "SELECT SUM(playcount) FROM album where SourceID<>6 and yearreleased={};".format(y)
    else:
        sql = "SELECT SUM(playcount) FROM album where SourceID<>6;"
    results = common.get_results(sql)
    return results[0][0]


def get_total_time(y):
    if y > 0:
        sql = "SELECT SUM(tracklength) FROM tracklengths INNER JOIN album on album.albumid = tracklengths.albumid " \
              "INNER JOIN log on log.albumid = album.albumid " \
              "where bonustrack = 0 and yearreleased={};".format(y)
    else:
        sql = "SELECT SUM(tracklength) FROM tracklengths INNER JOIN album on album.albumid = tracklengths.albumid " \
              "INNER JOIN log on log.albumid = album.albumid " \
              "where bonustrack = 0;"

    results = common.get_results(sql)
    return results[0][0]


def get_data(query, condition=None):
    sql = "SELECT ArtistName, Album, Points, Plays, AlbumID from {} ".format(query)

    if condition is not None:
        sql += "WHERE {} ".format(condition)

    sql += "LIMIT 100;".format(query.lower())

    return common.get_results(sql)


def generate_chart(outfile, data, basedir, y):
    totalplays = int(get_total_plays(y))
    totaltime = int(get_total_time(y))

    if len(data) > 0:
        f = io.open(os.path.join(basedir, outfile), "w", encoding='utf-8')
        header = "{:<5}{:<80}{:>10}{:>10}{:>10}\n".format("RANK","","TIME","FREQ","TOTAL")
        f.write(seperator)
        f.write(header)
        f.write(seperator)
        datadict = []
        rank = 1
        for dataline in data:
            art = dataline[0][:40]
            album = dataline[1]
            logtime = int(dataline[2])
            logcount = int(dataline[3])
            albumid=int(dataline[4])
            timeshare = (logtime / totaltime) * 100
            freqshare = (logcount / totalplays) * 100
            weighted_score = ((timeshare * 0.5) +(freqshare * 0.5))
            datadict_line = [art, album, albumid, timeshare, freqshare, weighted_score]
            datadict.append(datadict_line)
        s = sorted(datadict, key=lambda x: x[5], reverse=True)

        for row in s:
            art, album, albumid, timeshare, freqshare, score = row[:6]
            textline = "{:<5}{:<80}{:>10.2f}{:>10.2f}{:>10.2f}\n".format(rank, common.shorten_by_word(art.upper() + " / " + album , 80),
                                                                         timeshare, freqshare, score)
            f.write(textline)
            f.write(seperator)
            if y != 0:
                add_weighted_ranking(y, albumid, rank, score)
            rank += 1

        f.flush()
        f.close()


def add_weighted_ranking(y, albumid, rank, score):
    sql = "INSERT INTO annual_weighted_rankings VALUES ({}, {}, {}, {});".format(y, albumid, rank, score)
    common.execute_sql(sql)


def run():
    generate_chart("Album Chart (Weighted).txt", get_data("chart_album_alltime"), basedir, 0)
    common.execute_sql("TRUNCATE TABLE annual_weighted_rankings;")
    for y in range(2018, date.today().year + 1):
        generate_chart("Album Chart (Weighted) - {}.txt".format(y), get_data("charts_yearly", "YearReleased={}".format(y)), basedir + "/Yearly", y)

if __name__ == '__main__':
    run()