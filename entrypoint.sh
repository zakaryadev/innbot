#!/bin/bash
set -e

if [ ! -f "data.db" ]; then
    echo "No database found. Setting up from Excel files..."
    python db_setup_excel.py
else
    echo "Database already exists, skipping setup."
fi

echo "Starting bot..."
exec python bot.py
