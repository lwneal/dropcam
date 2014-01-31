import os
import sys
import getpass
import pickle
import requests
from requests.utils import cookiejar_from_dict, dict_from_cookiejar

LOGIN_API = 'https://www.dropcam.com/api/login.login'
CAMERAS_API_PATH = "https://www.dropcam.com/api/v1/cameras.get_visible"
COOKIE_CACHE = os.getenv("HOME") + '/.dropcam_cookie_cache'

def get_cookiejar(username=None, password=None):
  """ Use a cached cookiejar if available, else prompt the user to log in """
  def do_login():
    if username and password:
      return log_in_with_password(username=username, password=password)
    return log_in_with_password(**login_prompt())

  cached = load_from_file(COOKIE_CACHE)
  if cached:
    # Check if cached cookies still work
    resp = requests.get(url=CAMERAS_API_PATH, params={'group_cameras': True}, cookies=cached)
    if resp.ok and resp.json()['status'] == 0:
      return cached
    return do_login()
  else:
    return do_login()

def login_prompt():
  sys.stderr.write("Enter your Dropcam username: ")
  uname = raw_input('')
  sys.stderr.write("Password: ")
  passwd = getpass.getpass('')
  return {'username': uname, 'password': passwd}

def log_in_with_password(username, password):
  with requests.session() as c:
    c.post(LOGIN_API, data={'username':username, 'password':password})
    save_to_file(c.cookies, COOKIE_CACHE)
    return dict_from_cookiejar(c.cookies)

def save_to_file(data, fname):
  with open(fname, 'w') as outfile:
    pickle.dump(data, outfile)
  sys.stderr.write("NOTICE: Your session token has been saved in {0}\n".format(COOKIE_CACHE))
  
def load_from_file(fname):
  try:
    with open(fname) as infile:
      jar = pickle.load(infile)
      if any([c.is_expired() for c in jar]):
        return None
      return dict_from_cookiejar(jar)
  except Exception, e:
    return None
