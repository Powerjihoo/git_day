#!/bin/bash

# Ensure correct usage of the script
if [ "$#" -ne 3 ]; then
    echo "Usage: ./entrypoint.sh <file_path> <model_name> <device>"
    exit 1
fi

# Extract arguments
FILE_PATH=$1
MODEL_NAME=$2
DEVICE=$3

# Execute the Python script with the provided arguments
python3 vectorize.py --file_path "$FILE_PATH" --model_name "$MODEL_NAME" --device "$DEVICE"