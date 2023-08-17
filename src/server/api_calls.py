import requests
import constants

localhost = constants.LOCAL_HOST

# 1. Create a new record
def create_record(sensorID, user_id, time, file_path):
    # Define the URL of the endpoint
    url = f"{localhost}/{sensorID}/create"

    # Define the fields you want to send in addition to the file
    data = {
        'user_id': user_id,
        'time': time
    }

    with open(file_path, 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
        except requests.exceptions.RequestException as err:
            print(f"Request error: {err}")
        except Exception as err:
            print(f"Other error occurred: {err}")
    # Print the response
    print(response.text)
    
    
# 2. Get records
def get_records(sensorID, user_id, start_time, end_time):
    url = f"{localhost}/{sensorID}/records"

    params = {
        'user_id': user_id,
        'start_date': start_time,
        'end_date': end_time
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        records = response.json()
        # Process the retrieved records as needed
        print(records)
    else:
        print(f"Error: {response.status_code} - {response.text}")


# 3. Get record files
def get_files(sensorID, user_id, start_time, end_time):
    url = f"{localhost}/{sensorID}/records/files"
    
    params = {
        'user_id': user_id,
        'start_date': start_time,
        'end_date': end_time
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        # Save the zip file locally
        with open('files.zip', 'wb') as file:
            file.write(response.content)
        print("Files downloaded successfully.")
    else:
        print(f"Error: {response.status_code} - {response.text}")


# 4. Delete records
def delete_records(sensorID, user_id, start_time, end_time):
    url = f"{localhost}/{sensorID}/delete"

    params = {
        'user_id': user_id,
        'start_date': start_time,
        'end_date': end_time
    }

    response = requests.delete(url, params=params)

    if response.status_code == 200:
        print(response.text)
    else:
        print("Error:", response.text)


# 5. Delete all records 
def delete_all(sensorID):
    url = f"{localhost}/{sensorID}/delete"

    response = requests.delete(url)

    if response.status_code == 200:
        print(response.text)
    else:
        print("Error:", response.text)
        
        
# 6. Update records
def update_record(sensorID, user_id, start_time, end_time, updated_data):
    url = f"{localhost}/{sensorID}/records"
    
    params = {
        'user_id': user_id,
        'start_date': start_time,
        'end_date': end_time
    } 
    
    response = requests.put(url, params=params, json=updated_data)

    if response.status_code == 200:
        print("Record updated successfully.")
    else:
        print("Error:", response.text)


# Examples for calling each function
if __name__ == "__main__":
    
    sensorID = 'radar'  # Define the sensor type of the data record
    user_id = '1'

    # 1. Example of creating a new record
    file_path = "/1/2/3/example.txt"    # Define the path of the file you want to upload
    time = '2023-08-08 08:00:00'    # In the format 'YYYY-MM-DD HH:MM:SS', or None

    create_record(sensorID, user_id, time, file_path)


    # 2. Example of getting records
    start_time = '' # In the format 'YYYY-MM-DD HH:MM:SS', or None
    end_time = ''   # In the format 'YYYY-MM-DD HH:MM:SS', or None

    get_records(sensorID, user_id, start_time, end_time)


    # 3. Example of getting record files
    get_files(sensorID, user_id, start_time, end_time)
    
    
    # 4. Example of deleting records
    delete_records(sensorID, user_id, start_time, end_time)


    # 5. Example of deleting all records
    delete_all(sensorID)
    
    
    # 6. Example of updating records
    updated_data = {
            # fields and according values for replacement
            'time': '2023-09-09 09:00:00',
            'file': '/1/2/3/new_example.txt'
            
    }
    
    update_record(sensorID, user_id, start_time, end_time, updated_data)
