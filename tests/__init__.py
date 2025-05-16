import sys
import os
import logging

# Set the path to find the classes I'm testing against
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/caltskcts')))

# Turn off logging as this is just testing
logging.disable(logging.CRITICAL)
