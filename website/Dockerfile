# Dockerfile for the website

# Use a lightweight web server as a parent image
FROM nginx:alpine

# Set the working directory to /app/website
WORKDIR /app/website

# Copy the static files and templates into the container at /usr/share/nginx/html
COPY . /usr/share/nginx/html

# Expose port 80 to the outside world
EXPOSE 80

# Set the command to start the nginx server
CMD ["nginx", "-g", "daemon off;"]
