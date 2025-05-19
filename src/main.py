import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st

# This file is needed for Flask deployment structure
# It will redirect to the main Streamlit app
st.write("Redirecting to main application...")
