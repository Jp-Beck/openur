# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container (if your app uses a different port, replace 80 with that port number)
EXPOSE 80

# Define an entry point for the container. This is the command that will run when the container starts.
# Replace this with the command to run your application.
CMD ["python", "./openur.py"]