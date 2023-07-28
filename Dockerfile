# Dockerfile for the server

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /src

# Copy the current directory contents into the container at /app
COPY . /src

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port on which the server will run (change the port if needed)
EXPOSE 5000

# Set the command to run the server
CMD ["python", "server/app.py"]
