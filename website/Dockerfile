# Dockerfile for the website

# Use a lightweight web server as a parent image
FROM nginx:alpine

# Copy the static files and templates into the container at /usr/share/nginx/html
COPY ./website/static /usr/share/nginx/html/static
COPY ./website/templates /usr/share/nginx/html/templates

# Expose port 80 to the outside world
EXPOSE 80

# Set the command to start the nginx server
CMD ["nginx", "-g", "daemon off;"]
