from annual import artist_annual, album_annual, album_annual_new
from seasonal import artist_seasonal, album_seasonal
from alltime import artist_alltime, album_alltime, album_byformat
import logtools_common.logtools_common as common

common.execute_sql("TRUNCATE TABLE chart_history;")

artist_annual.run()
album_annual.run()
album_annual_new.run()

artist_seasonal.run()
album_seasonal.run()

artist_alltime.run()
album_alltime.run()
album_byformat.run()



