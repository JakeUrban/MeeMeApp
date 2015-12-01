"""
Configuration of 'memos' Flask app. 
Edit to fit development or deployment environment.

"""
import random 

### My local development environment
PORT=6789
DEBUG = True
GOOGLE_LICENSE_KEY = "../secretsProj6/client_keys.json"


### On ix.cs.uoregon.edu
#PORT=6789
#DEBUG = False # Because it's unsafe to run outside localhost
#GOOGLE_LICENSE_KEY = "../secretsProj6/client_keys.json"
