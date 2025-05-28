# Use the miniconda base image
FROM continuumio/miniconda3:24.9.2-0

# Set working directory
WORKDIR /usr/src/app

# Copy the environment.yml or requirements.txt into the image
COPY environment.yml /usr/src/app/environment.yml
COPY requirements.txt /usr/src/app/requirements.txt

# Create the Python environment
RUN conda env create -f environment.yml

# Copy the rest of the application code
COPY . /usr/src/app
RUN chmod +x /usr/src/app/entrypoint.sh

# Expose the necessary ports
EXPOSE 8000
EXPOSE 8501

# Execute the needed applications with the necessary commands
ENTRYPOINT ["/bin/bash", "/usr/src/app/entrypoint.sh"]
