import sqlite3, calendar
from random import randint
from datetime import datetime, timedelta, date


dbPath='/home/txapela/PersonalData/db/sens.db'
newTable='april2016'
tablePart='april2016'


db = sqlite3.connect(dbPath)
cursor=db.cursor()

for day in range(1,20):
    dayName = str(day).zfill(2) 
    dayNameTable = 'day_'+dayName+newTable
    cursor.execute('CREATE TABLE IF NOT EXISTS '+dayNameTable+'(time VARCHAR(255) NOT NULL, desc VARCHAR(255) NOT NULL, exercisetime VARCHAR(255) NOT NULL)')
    db.commit()
    consultTable = 'day_'+str(randint(20,30))+tablePart
    print (consultTable +' -> '+dayNameTable)

    cursor.execute('SELECT * from '+consultTable)
    rows = cursor.fetchall();
    for row in rows:
        cursor.execute('INSERT INTO '+dayNameTable+' VALUES (?,?,?)', (row[0], row[1], row[2]))
        db.commit()
            


