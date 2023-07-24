from flask import Flask, request, url_for, jsonify, redirect, send_file, make_response, render_template
from flask_pymongo import PyMongo
from datetime import datetime
import json
from bson import ObjectId
import io
import zipfile
from gridfs import GridFS
import constants
from flask_cors import CORS
from helper import switch_collection, query_by_filter
import os

template_folder=os.path.join(os.pardir, 'website', 'templates')
static_folder=os.path.join(os.pardir, 'website', 'static')
app = Flask(__name__, template_folder = template_folder, static_folder = static_folder)
# CORS(app)
app.config['MONGO_URI'] = constants.MONGO_URI
mongo = PyMongo (app)
# collection = mongo.db.radar
fs = GridFS(mongo.db)

allowed_extensions = constants.ALLOWED_EXTENSIONS
date_format = constants.DATE_FORMAT

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime(date_format)
        elif isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

app.json_encoder = CustomJSONEncoder
      
@app.route('/')
def index():
    return render_template('index.html')

# If error occurred, redirect to error page by calling: window.location.href = "/error";
@app.route("/error")
def handle_error():
    return redirect("error.html", code=500)

@app.route('/<string:sensorID>/create', methods= ['POST'])
def create_record(sensorID):
    collection = switch_collection(mongo, sensorID)
    file = request.files['file']
    
    if 'file' in request.files and file.filename:
        if file.filename.split('.')[-1].lower() in allowed_extensions:
            user_id = request.form.get('user_id')
            date_string = request.form.get('time')
        
            if user_id:
                if user_id.isdigit():
                    user_id = int(user_id)  # Convert user_id to numeric values if it's a string
                    # Check if Date field has input value
                    if date_string:
                        date_string = datetime.strptime(date_string, date_format)
                        # Check if record already exists
                        existing_record = collection.find_one({'user_id': user_id, 'time': date_string})
                        if existing_record:
                            return jsonify({"status": "Record with the same user_id and time exists."}), 400
                    else:
                        date_string = datetime.now().replace(microsecond=0, tzinfo=None)
                    
                    # file_id = mongo.save_file(file.filename, file)
                    file_id = fs.put(file, filename=file.filename)
                    
                    collection.insert_one({
                        'user_id': user_id, 
                        'time': date_string,
                        'file': file.filename,
                        'file_id': file_id
                        })
                    return jsonify({"status": "Document inserted."}), 200
                else:
                    return jsonify({"status": "User ID is not a valid integer."}), 400
            else:
                return jsonify({"status": "User ID needed."}), 400    
        else:
             return jsonify({"status": "Invalid file extension."}), 400             
    else:
        return jsonify({"status": "No file selected."}), 400
    
# # Route for handling the preflight request
# @app.route('/<string:sensorID>/records', methods=['OPTIONS'])
# def preflight(sensorID):
#     print("OPTIONS")
#     return _build_cors_preflight_response()

# def _build_cors_preflight_response():
#     response = make_response()
#     response.headers.add("Access-Control-Allow-Origin", "*")
#     response.headers.add('Access-Control-Allow-Headers', "*")
#     response.headers.add('Access-Control-Allow-Methods', "*")
#     return response

@app.route('/<string:sensorID>/records', methods=['GET'])
def get_records(sensorID):
    collection = switch_collection(mongo, sensorID)
    user_id = request.args.get('user_id')
    start_time = request.args.get('start_date')
    end_time = request.args.get('end_date')
    sort_by = request.args.get('sort')

    if user_id == '' or user_id.isdigit():     
        if user_id.isdigit():
            user_id = int(user_id)
        
        order = ['time', 'user_id'] if sort_by == 'time' else ['user_id', 'time']
        # Add sort parameter to the query
        query_sort = [(order[0], 1), (order[1], 1)]  # Sort by user_id ascending, then by time ascending
        
        query = query_by_filter(user_id, start_time, end_time)
        records = list(collection.find(query).sort(query_sort))
            
        if records:
            results = []
            for record in records: 
                new_record = {
                    'user_id': str(record['user_id']),  # Convert ObjectId to string
                    'time': record['time'].strftime(date_format),
                    'file':record['file']
                }
                results.append(new_record)
                print(str(record['user_id']))
                
            return _corsify_actual_response(jsonify(results)), 200
        else:
            return jsonify({"status": "No records found."}), 400 
    else:
        return jsonify({"status": "User ID is not a valid integer."}), 400
   

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response 

@app.route('/<string:sensorID>/records/files', methods=['GET'])
def get_files(sensorID):
    collection = switch_collection(mongo, sensorID)
    user_id = request.args.get('user_id')
    start_time = request.args.get('start_date')
    end_time = request.args.get('end_date')
    
    query = query_by_filter(user_id, start_time, end_time)
    records = list(collection.find(query))
    
    if records:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for record in records:
                file_obj = fs.find_one({'_id': record['file_id']})
                if file_obj:
                    file_data = fs.get(file_obj._id).read()
                    zip_file.writestr(record['file'], file_data)
                else:
                    print(f"File not found: {record['file']}")
    
        zip_buffer.seek(0)

        response = make_response(zip_buffer.getvalue())
        response.headers.set('Content-Type', 'application/zip')
        response.headers.set('Content-Disposition', 'attachment', filename='files.zip')

        return response, 200   
    else:
        return jsonify({"status": "No records found."}), 400 


@app.route('/<string:sensorID>/records/', methods=['PUT'])
def update_record(sensorID):
    collection = switch_collection(mongo, sensorID)

    # Get the updated data from the request body
    updated_data = request.get_json()
    user_id = updated_data.get('user_id')
    start_time = updated_data.get('start_date')
    end_time = updated_data.get('end_date')
        
    query = query_by_filter(user_id, start_time, end_time)
    records = list(collection.find(query))
    
    for record in records:
    # Update the record in the collection
        result = collection.update_one({'_id': ObjectId(record['_id'])}, {'$set': updated_data})

    if result.modified_count > 0:
        return jsonify({"status": "Record updated successfully."}), 200 
    else:
        return jsonify({"status": "Record not found or no changes made."}), 400 


@app.route('/<string:sensorID>/delete', methods=['DELETE'])
def delete_records(sensorID):
    collection = switch_collection(mongo, sensorID)
    user_id = request.args.get('user_id')
    start_time = request.args.get('start_date')
    end_time = request.args.get('end_date')
        
    query = query_by_filter(user_id, start_time, end_time)
    records = list(collection.find(query))
    if records:
        for record in records:
            # Delete the record from the collection
            collection.delete_one({'_id': ObjectId(record['_id'])})

            # Delete the corresponding file from GridFS
            file_metadata = fs.find_one({'_id': ObjectId(record['file_id'])})
            if file_metadata:
                # Delete the corresponding file from GridFS
                fs.delete(record['file_id'])
            else:
                print(f"File not found: {record['file']}")

        return jsonify({"status": "Record and associated file deleted."}), 200 
    else:
        return jsonify({"status": "Record not found."}), 400 
        

if __name__ == "__main__":
    app.run(debug=True)