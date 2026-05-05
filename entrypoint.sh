#!/bin/bash
set -e

echo "Setting up database..."
python db_setup.py

echo "Starting bot..."
exec python bot.py
