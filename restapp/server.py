#!/home/txapela/flask/bin/python

import sqlite3, calendar
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from flask import Flask, jsonify

app = Flask(__name__)
db_path = '/home/txapela/PersonalData/db/sens.db'

def get_aday(tstamp):
    datet = datetime.utcfromtimestamp(int(tstamp))
    table = datet.strftime('day_%d%B%Y').lower()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="'+table+'"')

    tablename = cursor.fetchall()

    if len(tablename) > 0:
        cursor.execute("SELECT * FROM "+table)

        rows = cursor.fetchall();
        data = []
        overActivities = {'walking': 0 , 'active': 0 }
        overTimes = {}

        if len(rows) > 0:
            for row in rows:
                data.append({'time':row[0], 'activity_name':row[1], 'activity_time':row[2]})
                
                if row[0] in overTimes:
                    overTimes[row[0]] += int(row[2])
                else:
                    overTimes[row[0]] = int(row[2])

                if row[1] in overActivities:
                    overActivities[row[1]] += int(row[2])
                else:
                    overActivities[row[1]] = int(row[2])


        return {'status': 'OK_ACK',
                'reason': 'TABLE_FOUND',
                'table': table,
                'overTimes': overTimes,
                'overActivities': overActivities,
                'date': datet.strftime('%d-%m-%Y_%H-%M-%S').lower(),
                'records': data}
    else:

        overActivities = {'walking': 0 , 'active': 0 }
        overTimes = {}

        return {'status': 'NOK_NACK',
                'reason': 'TABLE_NOT_FOUND',
                'table': table,
                'overTimes': overTimes,
                'overActivities': overActivities,
                'date': datet.strftime('%d-%m-%Y_%H-%M-%S').lower(),
                'records': []}      

def get_aweek(tstamp):
    theday = datetime.utcfromtimestamp(int(tstamp))
    days = {}
    overview = {'walking': 0 , 'active': 0 }
    tables = []

    for day in (range(1-theday.isoweekday(),0,1) + range(0,8-theday.isoweekday(),1) ): # time delta to each of other week day[m,t,x,th,f,s,s]
        
        newday=theday + timedelta(days=day)
        day_name = newday.strftime('%A').lower()
        days[day_name] = {}
        #dt = datetime.utcfromtimestamp(int(calendar.timegm(newday.utctimetuple())))
        table = newday.strftime('day_%d%B%Y').lower()
        tables.append(table)

        records = get_aday(calendar.timegm(newday.utctimetuple()))
        days[day_name] = records
        overview['walking'] += records['overActivities']['walking']
        overview['active'] += records['overActivities']['active']

    return {'status':'OK',
            'tables': tables,
            'overview': overview,
            'weekdata': days}

@app.route('/sens/api/v1.0/day/<tstamp>', methods=['GET'])
def get_day(tstamp):
    return jsonify(get_aday(tstamp))

@app.route('/sens/api/v1.0/week/<tstamp>', methods=['GET'])
def get_week(tstamp):
    return jsonify(get_aweek(tstamp))    

@app.route('/sens/api/v1.0/weekly/<tstamp>', methods=['GET'])
def get_weekly(tstamp):

    theday = datetime.utcfromtimestamp(int(tstamp))
    weeklyData = {}
    weeks = []

    for weekPast in range(6,-1,-1):        
        newday=theday - timedelta(days=weekPast*7)
        weekOfYear = newday.isocalendar()[1]+1
        year = newday.strftime('%Y').lower()
        nameWeek = 'week_'+str(weekOfYear)+'_'+year

        weeklyData[nameWeek] = {}
        weeklyData[nameWeek]['overview'] = {} 
        weeklyData[nameWeek]['weekpast'] = weekPast

        weeks.append(nameWeek)

        records = get_aweek(calendar.timegm(newday.utctimetuple()))
        weeklyData[nameWeek]['overview']['walking'] = records['overview']['walking']
        weeklyData[nameWeek]['overview']['active'] = records['overview']['active']

    return jsonify({'status':'OK',
                    'weeks' : weeks,
                    'weeklydata': weeklyData})

@app.route('/sens/api/v1.0/months/<tstamp>', methods=['GET'])
def get_months(tstamp):

    theday = datetime.utcfromtimestamp(int(tstamp))
    month_range = range(6,-1,-1) #get last 6 months, this and past 5. 
    months = {}
    
    for monthdiff in month_range:
        
        otherday = theday - relativedelta(months=monthdiff) #new day on another month
        month_name = otherday.strftime('%B_%Y').lower() #key of dict, month_year

        months[month_name] = {}
        months[month_name]['ref_timestamp'] = calendar.timegm(otherday.utctimetuple()) #insert ref info
        lastday = calendar.monthrange(otherday.year,otherday.month)[1] #last day of current month

        months[month_name]['days'] = {}
        months[month_name]['overview'] = {}
        months[month_name]['index'] = (len(month_range)-1) - monthdiff

        month_oview = months[month_name]['overview']
        month_oview['wholemonth'] = 0
        month_oview['walking'] = 0
        month_oview['active'] = 0

        for day in range(1,lastday+1,1): #all days of current month [1..28] or [1..30] or [1..31]
            #print(str(day)+'_'+month_name)
            check_day = otherday.replace(day=day) #Repalce day for 1st,2nd..31th of each month
            months[month_name]['days'][str(day)+'_'+month_name] = {}
            current_day = months[month_name]['days'][str(day)+'_'+month_name]
            current_day['allday'] = 0
            current_day['walking'] = 0
            current_day['active'] = 0

            records = get_aday(calendar.timegm(check_day.utctimetuple()))
            data = records['records']
            
            if len(data) > 0:
                current_day['walking'] = records['overActivities']['walking']
                current_day['active'] = records['overActivities']['active']
                current_day['allday'] = current_day['walking'] + current_day['active']

                month_oview['walking'] += current_day['walking']
                month_oview['active'] += current_day['active']
                month_oview['wholemonth'] += current_day['allday']

    return jsonify({'status':'OK',
                    'monthsdata': months})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True) 
