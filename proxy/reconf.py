#!/usr/bin/python

import requests
import sqlite3
import logging
import sys
import simplegmail
from datetime import datetime

dbPath='/home/txapela/PersonalData/db/sens.db'
table='april2016'
offset = 7200

db = sqlite3.connect(dbPath)
cursor=db.cursor()

cursor.execute('SELECT * from '+table)

data = cursor.fetchall()
    
for record in data:
    datet=datetime.utcfromtimestamp(int(record[0])+offset)
    monthtable=datet.strftime('%B%Y').lower()
    print(monthtable)
    daytable=datet.strftime('day_%d%B%Y').lower()
    print(monthtable+" - "+daytable)
    cursor.execute('CREATE TABLE IF NOT EXISTS '+monthtable+'(time VARCHAR(255) PRIMARY KEY NOT NULL, type VARCHAR VARCHAR(255) NOT NULL, desc VARCHAR VARCHAR(255) NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS '+daytable+'(time VARCHAR(255) NOT NULL, desc VARCHAR(255) NOT NULL, exercisetime VARCHAR(255) NOT NULL)')
    db.commit()

    currentTime=datet.strftime('%H')+':00'

    if record[2]=='walking' or record[2]=='active':
        print("Active or walking... -> Entering")
        cursor.execute('SELECT exercisetime from '+daytable+' WHERE time="'+currentTime+'" AND desc="'+record[2]+'"')

        exTime=cursor.fetchone()           

        if exTime:
            rec=str(record)
            print("record: "+rec+" - ctime: "+currentTime+" - extTime: "+exTime[0])
            newtime=str(int(exTime[0])+10)

            cursor.execute('UPDATE '+daytable+' SET exercisetime="'+newtime+'" WHERE time="'+currentTime+'" AND desc="'+record[2]+'"')
            db.commit()
        else:
            cursor.execute('INSERT INTO '+daytable+' VALUES (?,?,?)', (currentTime, record[2], '10'))
            db.commit()

    if(monthtable != 'april2016'):
        cursor.execute('INSERT OR REPLACE INTO '+monthtable+' VALUES (?,?,?)', record)
        db.commit()
