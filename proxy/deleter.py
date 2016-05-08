import requests
import sqlite3
import logging
import sys
import simplegmail
from datetime import datetime

dbPath='/home/txapela/PersonalData/db/sens.db'

db = sqlite3.connect(dbPath)
cursor=db.cursor()

cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')

data = cursor.fetchall()
    
for d in data:
	if d[0].startswith('day'):
		cursor.execute('DROP table '+d[0])


