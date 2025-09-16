import streamlit as st
import sys
import os

# Add parent directory to path to import from main files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main app functions
from ledger_app import *

# This will run the ledger app as a page
if __name__ == "__main__":
    main()
