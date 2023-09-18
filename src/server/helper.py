from datetime import datetime
from flask import jsonify
import constants

sensors = constants.SENSOR_LIST

def switch_collection(mongo, sensorID):
    sensor_map = {sensor: getattr(mongo.db, sensor) for sensor in sensors}
      
    try:
        collection = sensor_map[sensorID]
        return collection
    except KeyError:
        raise ValueError(f"Invalid sensorID: {sensorID}")

def check_date_format(date):
    datetime_format = '%Y-%m-%d %H:%M:%S'
    date_format = '%Y-%m-%d'
    start_datetime = None

    if date:
        try:
            start_datetime = datetime.strptime(date, datetime_format)
        except ValueError:
            try:
                start_datetime = datetime.strptime(date, date_format)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
    
    return start_datetime

def query_by_filter(user_id, start_time, end_time):
    start_datetime = check_date_format(start_time)
    end_datetime = check_date_format(end_time)
     
    query = {}
    if user_id:
        query['user_id'] = user_id

    if start_time or end_time:
        query['time'] = {}
        
        if start_time:
            query['time']['$gte'] = start_datetime
        
        if end_time:
            query['time']['$lte'] = end_datetime
            
    return query

def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, '%d/%m/%Y')
        return True
    except ValueError:
        return False