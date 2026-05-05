#!/bin/bash
set -e

echo "Setting up database from Excel files..."
python db_setup_excel.py

echo "Starting bot..."
exec python bot.py
