#!/usr/bin/python

import requests
import sqlite3
import logging
import sys
import simplegmail
from datetime import datetime

dbPath='/home/txapela/PersonalData/db/sens.db'
logName='proc.log'
logPath='/home/txapela/PersonalData/logs/proxy/'
checktable='checks'
session='393'

logging.basicConfig(filename=logPath+logName,level=logging.INFO)


db = sqlite3.connect(dbPath)
cursor=db.cursor()


if(len(sys.argv) > 1):
    timestamp=sys.argv[1]
    if(len(sys.argv) > 2):
        session=sys.argv[2]
else:
    cursor.execute('SELECT tstamp FROM '+checktable+' WHERE type="lastCheck"')
    timestamp=cursor.fetchone()[0] # put in in the following string +timestamp


logging.info('+++++ NEW FETCH ('+timestamp+'): '+str(datetime.now())+' +++++')

url='URL'+session+'/'+timestamp

try:
    response = requests.get(url)
    logging.info('Sent request: '+url)
except requests.exceptions.Timeout:
    logging.error('Timeout on '+url)
except requests.exceptions.RequestException as e:
    logging.error('EXCEPTION: '+e)
    logging.info('+++++ CLOSING FETCH ('+timestamp+'): '+str(datetime.now())+' +++++')
    sys.exit(1)

data = response.json()

if data['result_text']=='OK':
    data = response.json()['value']['data']
    counter=0
    countEx=0

    for record in data:
        counter+=1
        #Convert everything to Strng, it is easier like that. When retireving, we'll hanldle the
        #str->number conversion if needed.
        for idx, value in enumerate(record):
            if type(value) == float and idx == 0:
                record[idx]=('%.2f' % (value,)).rstrip('0').rstrip('.')[:-3]
            else:
                record[idx]=str(value)
    
        #Make sure all tables exist and everything is up
        datet=datetime.utcfromtimestamp(int(record[0])+7200)
    
        monthtable=datet.strftime('%B%Y').lower()
        daytable=datet.strftime('day_%d%B%Y').lower()
        cursor.execute('CREATE TABLE IF NOT EXISTS '+monthtable+'(time VARCHAR(255) PRIMARY KEY NOT NULL, type VARCHAR VARCHAR(255) NOT NULL, desc VARCHAR VARCHAR(255) NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS '+daytable+'(time VARCHAR(255) NOT NULL, desc VARCHAR(255) NOT NULL, exercisetime VARCHAR(255) NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS '+checktable+'(ID INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, tstamp TEXT NOT NULL)')
        db.commit()
  
        #Insert exercised time on day table, walk or active. 
        currentTime=datet.strftime('%H')+':00'
 
        if record[2]=='walking' or record[2]=='active':
            countEx+=1
            cursor.execute('SELECT exercisetime from '+daytable+' WHERE time="'+currentTime+'" AND desc="'+record[2]+'"')

            exTime=cursor.fetchone()           
    
            if exTime:
                rec=str(record)
                newtime=str(int(exTime[0])+10)

                cursor.execute('UPDATE '+daytable+' SET exercisetime="'+newtime+'" WHERE time="'+currentTime+'" AND desc="'+record[2]+'"')
                db.commit()
            else:
                cursor.execute('INSERT INTO '+daytable+' VALUES (?,?,?)', (currentTime, record[2], '10'))
                db.commit()
    
        cursor.execute('INSERT OR REPLACE INTO '+monthtable+' VALUES (?,?,?)', record)
        db.commit()
    
    logging.info('COLLECTED RECORDS: '+str(counter))
    logging.info('RELEVANT RECORDS: '+str(countEx))
    cursor.execute('INSERT INTO '+checktable+'(type,tstamp) VALUES (?,?)', ('check',timestamp))
    db.commit()

    lastCheck=data[-1][0]
    logging.info('LAST RECORD, NEXT FIRST CHECK: '+lastCheck)
    cursor.execute('SELECT * FROM '+checktable+' WHERE type="lastCheck"')

    if cursor.fetchone():
        cursor.execute('UPDATE '+checktable+' SET tstamp="'+lastCheck+'" WHERE type="lastCheck"')
    else:
        cursor.execute('INSERT INTO '+checktable+'(type,tstamp) VALUES (?,?)', ('lastCheck',lastCheck))
        
    db.commit()
   
else:
    cursor.execute('INSERT INTO '+checktable+'(type,tstamp) VALUES (?,?)', ('check',timestamp))
    db.commit()

    logging.error('No records for: '+session+' '+timestamp)
    message='No records found\n'
    message+='Link: '+url+'\n'
    message+='Time stamp checked: '+str(datetime.utcfromtimestamp(int(timestamp)))
    #simplegmail.sendMail("ganer77@gmail.com",message,"ALERT FROM Sens Proxy")

logging.info('+++++ CLOSING FETCH ('+timestamp+'): '+str(datetime.now())+' +++++\n\n')
