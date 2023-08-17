
var sensors = ['radar', 'camera', 'oximeter', 'wave'];
var recordsPerPage = 10;
var sortBy = 'time';    // 'time' or 'user_id'

function createSensorButtons() {
    var sensorButtonsContainer = document.getElementById('sensorButtonsContainer');
  
    sensors.forEach(function(sensor) {
        var button = document.createElement('button');
        button.id = sensor + '-button';
        button.className = 'sensor-button';
        button.textContent = sensor.charAt(0).toUpperCase() + sensor.slice(1);
        sensorButtonsContainer.appendChild(button);
      });
  }
  
  // Call the function to create the sensor buttons
  createSensorButtons();

// JavaScript function to handle sensor selection
function selectSensor(sensorID) {
    // Toggle the selected state of the button; Set the sensor ID based on selected button
    sensors.forEach(function (sensor) {
      var button = document.getElementById(sensor + '-button');
      if (sensor === sensorID) {
        button.classList.toggle('selected');
        if (button.classList.contains('selected')) {
            sensorID = sensor;
          }
      } else {
        button.classList.remove('selected');
      }
    });
  
    // Set the sensor ID in the form action URL
    var createRecordForm = document.getElementById('createRecordForm');
    createRecordForm.action = '/' + sensorID + '/create';
  
    var getRecordsForm = document.getElementById('getRecordsForm');
    getRecordsForm.action = '/' + sensorID + '/records';
  }
  
  // Function to get the selected sensor ID
  function getSelectedSensorID() {
    var selectedSensor = '';
    sensors.forEach(function (sensor) {
      var button = document.getElementById(sensor + '-button');
      if (button.classList.contains('selected')) {
        selectedSensor = sensor;
      }
    });
    if (selectedSensor === '') {
      alert('No sensor selected!');
    }
    return selectedSensor;
  }

// Function to handle create record button click
function createRecordButtonClick(event) {
    event.preventDefault();

    var sensorID = getSelectedSensorID();
    var formData = new FormData(createRecordForm);
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/' + sensorID + '/create', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4){
            if (xhr.status === 200) {
                // Request successful, handle the response here
                var errorResponse = JSON.parse(xhr.responseText);
                var errorMessage = errorResponse.status;
                alert(errorMessage);
            } else {
                // Request failed, handle the error here
                var errorResponse = JSON.parse(xhr.responseText);
                var errorMessage = errorResponse.status;
                console.log(`status = ${xhr.status}; errorMessage = ${errorMessage}`);
                alert(errorMessage);
            }
        }
    };
    xhr.send(formData);
}

// Global variables
var currentPage = 1;
var totalRecords = 0;
var totalPages = 0;
var records = ''; // Declare the records variable in a global scope

// Function to handle get records button click
function getRecordsButtonClick(event) {

    var sensorID = getSelectedSensorID();
    var formData = new FormData(getRecordsForm);
    var params = new URLSearchParams(formData).toString(); // Convert form data to URL query parameters

    // Append sortBy parameter to the query string
    if (sortBy) {
        params += '&sort=' + sortBy;
    }
    
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/' + sensorID + '/records?' + params, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                // Request successful, handle the response here
                records = JSON.parse(xhr.responseText);
                currentPage = 1;
                displayRecords();
            } else {
                // Request failed, handle the error here
                var errorResponse = JSON.parse(xhr.responseText);
                var errorMessage = errorResponse.status;
                console.log(`readyState = ${xhr.readyState}; status = ${xhr.status}; errorMessage = ${errorMessage}`);
                alert(errorMessage);
            }
        }
    };
    xhr.send();
    event.preventDefault();

}

// Function to handle download records button click
function downloadRecordsButtonClick(event) {

    var sensorID = getSelectedSensorID();
    var formData = new FormData(getRecordsForm);
    var params = new URLSearchParams(formData).toString(); // Convert form data to URL query parameters

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/' + sensorID + '/records/files?' + params, true);
    xhr.responseType = 'blob'; // Set the response type to 'blob' for binary data
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
            // Request successful, handle the response here
            var blob = xhr.response;
            saveBlobAsFile(blob, 'files.zip'); // Call a helper function to save the blob as a file
            } else {
                // Request failed, handle the error here
                var errorMessage = "No records found.";
                console.log(`readyState = ${xhr.readyState}; status = ${xhr.status}; errorMessage = ${errorMessage}`);
                alert(errorMessage);
            }
        }
    };
    xhr.send();
    event.preventDefault();
}

// Helper function to save the blob as a file
function saveBlobAsFile(blob, fileName) {
    var link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = fileName;
    link.click();
    window.URL.revokeObjectURL(link.href);
}

// Function to display records
function displayRecords() {
    totalRecords = records.length
    totalPages = Math.ceil(totalRecords / recordsPerPage);
    var startIndex = (currentPage - 1) * recordsPerPage;
    var endIndex = startIndex + recordsPerPage;
    var recordsToShow = records.slice(startIndex, endIndex);


    var tableBody = document.querySelector('#recordsTable tbody');
    tableBody.innerHTML = '';

    recordsToShow.forEach(function(record) {
        var row = document.createElement('tr');
        var userIDCell = document.createElement('td');
        var timeCell = document.createElement('td');
        var fileCell = document.createElement('td');

        userIDCell.textContent = record.user_id;
        timeCell.textContent = record.time;
        fileCell.textContent = record.file;

        row.appendChild(userIDCell);
        row.appendChild(timeCell);
        row.appendChild(fileCell);

        tableBody.appendChild(row);
    });

    var pagination = document.getElementById('pagination');
    var prevPageButton = document.getElementById('prevPageButton');
    var nextPageButton = document.getElementById('nextPageButton');
    var currentPageSpan = document.getElementById('currentPage');

    currentPageSpan.textContent = currentPage + ' / ' + totalPages;

    if (currentPage === 1) {
        prevPageButton.disabled = true;
    } else {
        prevPageButton.disabled = false;
    }

    if (endIndex >= totalRecords) {
        nextPageButton.disabled = true;
    } else {
        nextPageButton.disabled = false;
    }
}

// Function to handle previous page button click
function prevPageButtonClick() {
    if (currentPage > 1) {
        currentPage--;
        displayRecords();
    }
}

// Function to handle next page button click
function nextPageButtonClick() {
    if (currentPage < totalPages) {
        currentPage++;
        displayRecords();
    }
}

// Attach event listeners
// Loop through the sensors array
  sensors.forEach(function(sensor) {
    document.getElementById(sensor + '-button').addEventListener('click', function() {
        selectSensor(sensor);
      });
  });
document.getElementById('createRecordButton').addEventListener('click', createRecordButtonClick);
document.getElementById('getRecordsButton').addEventListener('click', getRecordsButtonClick);
document.getElementById('downloadRecordsButton').addEventListener('click', downloadRecordsButtonClick);
document.getElementById('prevPageButton').addEventListener('click', prevPageButtonClick);
document.getElementById('nextPageButton').addEventListener('click', nextPageButtonClick);


// Global variables
var sortByUserIdButton = document.getElementById('sortByUserIdButton');
var sortByTimeButton = document.getElementById('sortByTimeButton');
var sortByUserId = false; // Initially not sorted by User ID
var sortByTime = false; // Initially not sorted by Time

// Function to handle sort by User ID button click
function sortByUserIdButtonClick() {
    if (!sortByUserId) {
        sortByUserId = true;
        sortByTime = false;
        sortByUserIdButton.classList.add('selected');
        sortByTimeButton.classList.remove('selected');
        // Perform sorting by User ID
        // Call a function to fetch records sorted by User ID
        sortBy = 'user_id';
        getRecordsButtonClick(event);

    }
}

// Function to handle sort by Time button click
function sortByTimeButtonClick() {
    if (!sortByTime) {
        sortByTime = true;
        sortByUserId = false;
        sortByTimeButton.classList.add('selected');
        sortByUserIdButton.classList.remove('selected');
        // Perform sorting by Time
        // Call a function to fetch records sorted by Time
        sortBy = 'time';
        getRecordsButtonClick(event);

    }
}

// Attach event listeners
sortByUserIdButton.addEventListener('click', sortByUserIdButtonClick);
sortByTimeButton.addEventListener('click', sortByTimeButtonClick);
