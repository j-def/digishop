import pyodbc
from data_manager import manager
import datetime
dbserver = 'REGCONSERVER1'
dbdatabase = 'digishop'
dbusername = 'belotecainventory'
dbpassword = 'belotecainventory'
cnxn = pyodbc.connect(
    'DRIVER={SQL Server};SERVER=' + dbserver + ';DATABASE=' + dbdatabase + ';UID=' + dbusername + ';PWD=' + dbpassword)
cursor = cnxn.cursor()
cursor.execute("SELECT moment_id, MIN(price) FROM listings GROUP BY moment_id")
filters =
print(cursor.fetchall())