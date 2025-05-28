# Use the official Python image from the Docker Hub
FROM python:3.9.20


# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt /app/

# Install any necessary dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project source into the container
COPY . /app/

# Run the main.py when the container launches
CMD ["python", "src/main.py"]