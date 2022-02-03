#!/bin/bash

if ! command -v gs &> /dev/null; then
    printf "Error: The 'gs' command was not found. Please install Ghostscript.\n"
fi

for filename in "$@"; do
    printf "Compressing %s...\n" "$filename"
    mv "$filename" "$filename.original"
    gs \
        -sDEVICE=pdfwrite \
        -dCompatibilityLevel=1.4 \
        -dNOPAUSE \
        -dQUIET \
        -dBATCH \
        -sOutputFile="$filename" \
        "$filename.original"
    rm -f "$filename.original"
done
