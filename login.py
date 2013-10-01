import os
import sys
import getpass
import json
import requests
from requests.utils import cookiejar_from_dict, dict_from_cookiejar

LOGIN_API = 'https://www.dropcam.com/api/login.login'
COOKIE_CACHE = os.getenv("HOME") + '/.dropcam_cookie_cache'

def get_cookiejar(username=None, password=None):
  """ Use a cached cookiejar if available, else prompt the user to log in """
  cached = load_from_file(COOKIE_CACHE)
  if cached:
    return cookiejar_from_dict(cached)
  elif username and password:
    return login_with_password(username=username, password=password)
  else:
    return login_with_password(**login_prompt())

def login_prompt():
  sys.stderr.write("Enter your Dropcam username: ")
  uname = raw_input('')
  sys.stderr.write("Password: ")
  passwd = getpass.getpass('')
  return {'username': uname, 'password': passwd}

def login_with_password(username, password):
  with requests.session() as c:
    c.post(LOGIN_API, data={'username':username, 'password':password})
    cookies = dict_from_cookiejar(c.cookies)
    if not cookies:
      raise Exception("Bad username or password")
    save_to_file(cookies, COOKIE_CACHE)
    return cookies

def save_to_file(stuff_to_save, fname):
  with open(fname, 'w') as outfile:
    outfile.write(json.dumps(stuff_to_save))
  sys.stderr.write("NOTICE: Your session token has been saved in {0}\n".format(COOKIE_CACHE))
  
def load_from_file(fname):
  try:
    with open(fname) as infile:
      return json.loads(infile.read())
  except IOError:
    pass
  return None
