# Dockerfile for the server

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# Set the command to run the server
CMD ["python", "app.py"]


# FROM python:3.10

# COPY . /app

# WORKDIR /app

# RUN pip install -r requirements.txt

# EXPOSE 5000

# CMD ["python", "app.py"]
