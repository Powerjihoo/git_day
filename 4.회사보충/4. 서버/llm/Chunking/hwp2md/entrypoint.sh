#!/bin/bash

# conda 환경 활성화
source /opt/conda/etc/profile.d/conda.sh
conda activate hwp2md

# Check the number of arguments
if [ "$#" -ne 3 ]; then
    echo "Usage: ./entrypoint.sh <hwp2html|html2md> <input_file> <output_file>"
    exit 1
fi

# Extract arguments
COMMAND=$1
INPUT_FILE=$2
OUTPUT_FILE=$3

# Execute the appropriate script based on the command
case $COMMAND in
    hwp2html)
        python src/hwp2html.py -h "$INPUT_FILE" -d "$OUTPUT_FILE"
        ;;
    html2md)
        python src/html2md.py -h "$INPUT_FILE" -m "$OUTPUT_FILE"
        ;;
    *)
        echo "Invalid command. Use 'hwp2html' for converting HWP to HTML or 'html2md' for converting HTML to Markdown."
        exit 1
        ;;
esac