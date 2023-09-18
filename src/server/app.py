from flask import Flask, request, url_for, jsonify, redirect, send_file, make_response, render_template
from flask_pymongo import PyMongo
from datetime import datetime
import json
from bson import ObjectId
import io
import zipfile
from gridfs import GridFS
import constants
# from flask_cors import CORS
from helper import switch_collection, query_by_filter, is_valid_date, check_date_format
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
            date_string = request.form.get('time')
            name = request.form.get('name')
            dob = request.form.get('dob')
            sex = request.form.get('sex')
            high_bp = request.form.get('high_bp')
            actual_sbp = request.form.get('actual_sbp')
            actual_dbp = request.form.get('actual_dbp')

            if name:
                name_without_spaces = name.replace(" ", "")
                if name_without_spaces.isalpha():
                    # Check if the user exists in the "users" collection
                    users_collection = mongo.db['users']
                    existing_user = users_collection.find_one({'name': name})

                    if existing_user:
                        user_id = existing_user['user_id']
                    else:
                        # If the user doesn't exist, count the number of documents in the "users" collection
                        user_count = users_collection.count_documents({})
                        # Assign the new user an ID of count+1
                        user_id = user_count + 1
                        
                        if not is_valid_date(dob):
                            return jsonify({"status": "DOB should be in the format 'dd/mm/yyyy'."}), 400

                        if sex not in ['M', 'F']:
                            return jsonify({"status": "Sex should be 'M' or 'F'."}), 400

                        if high_bp not in ['Y', 'N']:
                            return jsonify({"status": "High BP should be 'Y' or 'N'."}), 400

                    # Check if Date field has input value
                    if date_string:
                        date_string = datetime.strptime(date_string, date_format)
                        # Check if record already exists
                        existing_record = collection.find_one({'user_id': user_id, 'time': date_string})
                        if existing_record:
                            return jsonify({"status": "Record with the same user_id and time exists."}), 400
                    else:
                        date_string = datetime.now().replace(microsecond=0, tzinfo=None)

                    # Prepare user data for insertion or update in the "users" collection
                    user_data = {
                        'user_id': user_id,
                        'name': name,
                        'dob': dob,
                        'sex': sex,
                        'high_bp': high_bp
                    }

                    # Remove fields with None or empty values from user_data
                    user_data = {key: value for key, value in user_data.items() if value is not None and value != ''}

                    if existing_user:
                        # Update user information in the "users" collection
                        users_collection.update_one({'user_id': user_id}, {'$set': user_data})
                    else:
                        # Insert new user information if the user doesn't exist
                        users_collection.insert_one(user_data)

                    # file_id = mongo.save_file(file.filename, file)
                    file_id = fs.put(file, filename=file.filename)
                    
                    collection.insert_one({
                        'user_id': user_id,
                        'name': name, 
                        'time': date_string,                        
                        'actual_sbp': actual_sbp,
                        'actual_dbp': actual_dbp,
                        'file': file.filename,
                        'file_id': file_id
                        })
                    return jsonify({"status": "Document inserted."}), 200
                else:
                    return jsonify({"status": "Name should contain only letters."}), 400
            else:
                return jsonify({"status": "Name is required."}), 400    
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
    name = request.args.get('name')  # Add 'name' parameter
    start_time = request.args.get('start_date')
    end_time = request.args.get('end_date')
    sort_by = request.args.get('sort')

    users_collection = mongo.db['users']
    # order = ['time', 'user_id'] if sort_by == 'time' else ['user_id', 'time']
    # # Add sort parameter to the query
    # query_sort = [(order[0], 1), (order[1], 1)]  # Sort by user_id ascending, then by time ascending

    if name:
        # Find the user_info based on the provided name
        user_info = users_collection.find_one({'name': name})
        if user_info:
            user_id = user_info['user_id']
            print(name)
            print(user_id)
        else:
            return jsonify({"status": "User not found in the 'users' collection."}), 400
    elif user_id:
        if user_id.isdigit():
            user_id = int(user_id)
            # Check if the user exists in the "users" collection
            user_info = users_collection.find_one({'user_id': user_id})
            if not user_info:
                return jsonify({"status": "User not found in the 'users' collection."}), 400
        else:
            return jsonify({"status": "User ID is not a valid integer."}), 400
    else:
        user_info = ''

    # Define the aggregation pipeline based on user_id (if provided)
    pipeline = []

# Add $match stage for user_id
    if user_id:
        id_match_stage = {
            "$match": {
                "user_id": user_id
            }
        }
        pipeline.append(id_match_stage)

    # Add $match stage for time range filtering
    time_match = {}

    if start_time:
        time_match['$gte'] = check_date_format(start_time)

    if end_time:
        time_match['$lte'] = check_date_format(end_time)

    if time_match:
        time_match_stage = {
            "$match": {
                "time": time_match
            }
        }
        pipeline.append(time_match_stage)

    pipeline.extend(
        [
            {
                "$sort": {
                    "user_id": 1,
                    "time": 1 if sort_by == 'time' else -1
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "user_id",
                    "as": "user_info"
                }
            },
            {
                "$unwind": "$user_info"
            },
            {
                "$project": {
                    "_id": 0,
                    "user_id": 1,
                    "name": "$user_info.name",
                    "dob": "$user_info.dob",
                    "sex": "$user_info.sex",
                    "high_bp": "$user_info.high_bp",
                    "actual_sbp": 1,
                    "actual_dbp": 1,
                    "time": {"$dateToString": {"format": date_format, "date": "$time"}},
                    "file": 1
                }
            }
        ]
    )

    # Execute the aggregation pipeline
    records = list(collection.aggregate(pipeline))

    if records:
        return _corsify_actual_response(jsonify(records)), 200
    else:
        return jsonify({"status": "No records found."}), 400

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response 

@app.route('/<string:sensorID>/records/files', methods=['GET'])
def get_files(sensorID):
    collection = switch_collection(mongo, sensorID)
    user_id = request.args.get('user_id')
    name = request.args.get('name')
    start_time = request.args.get('start_date')
    end_time = request.args.get('end_date')
    
    user_id = int(user_id)
    if not user_id and name:
        user_info = collection.find_one({'name': name})
        user_id = user_info['user_id']

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
    user_id = request.args.get('user_id')
    name = request.args.get('name')
    start_time = request.args.get('start_date')
    end_time = request.args.get('end_date')

    user_id = int(user_id)
    if not user_id and name:
        user_info = collection.find_one({'name': name})
        user_id = user_info['user_id']
            
    query = query_by_filter(user_id, start_time, end_time)
    records = list(collection.find(query))
    
    for record in records:
    # Update the record in the collection
        result = collection.update_one({'_id': ObjectId(record['_id'])}, {'$set': updated_data})

    if result.modified_count > 0:
        return jsonify({"status": "Record updated successfully."}), 200 
    else:
        return jsonify({"status": "Record not found or no changes made."}), 400 

@app.route('/<string:sensorID>/users/', methods=['PUT'])
def update_user(sensorID):
    collection = mongo.db['users']

    # Get the updated data from the request body
    updated_data = request.get_json()
    user_id = request.args.get('user_id')
    name = request.args.get('name')
    start_time = request.args.get('start_date')
    end_time = request.args.get('end_date')

    user_id = int(user_id)
    if not user_id and name:
        user_info = collection.find_one({'name': name})
        user_id = user_info['user_id']
            
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
    name = request.args.get('name')
    start_time = request.args.get('start_date')
    end_time = request.args.get('end_date')
        
    user_id = int(user_id)
    if not user_id and name:
        user_info = collection.find_one({'name': name})
        user_id = user_info['user_id']
        
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
    app.run(host='0.0.0.0', port=8000, debug=True)
    # app.run(debug=True)