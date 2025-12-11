# -*- coding: utf-8 -*-
"""
Database Initialization Script
Run this to set up the SQLite database
"""

from database import init_database

if __name__ == '__main__':
    print("Setting up database...")
    init_database()
    print("Done!")
