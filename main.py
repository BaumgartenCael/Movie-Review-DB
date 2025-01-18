#
# Client-side python app for benford app, which is calling
# a set of lambda functions in AWS through API Gateway.
# The overall purpose of the app is to process a PDF and
# see if the numeric values in the PDF adhere to Benford's
# law.
# Authors:
#  Brianna Perez, Cael Baumgarten, Aidan Mott
#
#   Prof. Joe Hummel (initial template)
#   Northwestern University
#   CS 310
#CLIENT SIDE TEMPLATE USED FROM PROJECT 3
import datatier
import requests
import json
import uuid
import pathlib
import logging
import sys
import os
import base64
import time
import random
from configparser import ConfigParser
import matplotlib.pyplot as plt
############################################################
#
# classes
#
class User:

  def __init__(self, row):
    self.userid = row[0]
    self.firstname = row[1]
    self.lastname = row[2]
class Review:

  def __init__(self, row):
    self.reviewid = row[0]
    self.userid = row[1]
    self.moviename = row[2]
    self.rating = row[3]
    self.review = row[4]
    self.genre = row[5]


###################################################################
#
# web_service_get
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_get(url):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.get(url)
        
      if response.status_code in [200, 400, 480, 481, 482, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
  
      #
      # if get here, we tried 3 times, we give up:
      #
      break
    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_get() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
    

############################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number

  Parameters
  ----------
  None
  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """
  try:
    print()
    print(">> Enter a command:")
    print("   0 => end")
    print("   1 => add review")
    print("   2 => get recommendations")
    print("   3 => get my movie stats")
    print("   4 => find my userid")
    # print("   4 => upload pdf")
    # print("   5 => download results")
    # print("   6 => upload and poll")

    cmd = input()

    if cmd == "":
      cmd = -1
    elif not cmd.isnumeric():
      cmd = -1
    else:
      cmd = int(cmd)

    return cmd

  except Exception as e:
    print("**ERROR")
    print("**ERROR: invalid input")
    print("**ERROR")
    return -1


############################################################
#
# users
#
def add_review(baseurl):
  """
  Prints out all the users in the database

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    firstname=input("Please enter your first name: ")
    lastname=input("Please enter your last name: ")
    moviename=input("Please enter a name of a movie: ")
    rating=input("What would you rate this movie out of 10? please only use integers: ")
    if rating.isdigit() == False or int(rating) >10:
      print("Rating must be an integer between 0 and 10")
      # raise Exception("Please only input positive integers <= 10 into rating ")
      return
    
    review=input(f'Write a review of {moviename}: ')
    data ={'firstname':firstname,'lastname':lastname,'moviename':moviename,"rating":rating,"review":review}

    api = '/add_review'
    url = baseurl + api
    res = requests.put(url,json.dumps(data))
    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500 or res.status_code>= 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return
    #
    # deserialize and extract users:
    #
    body = res.json()
    # #
    print(body)
    print(f'Review added for user {firstname} {lastname}')
    return

  except Exception as e:
    logging.error("**ERROR: add_review() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


############################################################
#
# jobs
#
def get_rec(baseurl):
  """
  Get movie recommendations 
  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    userid=input("Please enter your userid: ")
    api = '/recommend/'+userid
    url = baseurl + api

    # res = requests.get(url)
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500 or res.status_code>= 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # deserialize and extract jobs:
    #
    body = res.json()
    
    #
    # Now we can think OOP:
    #
    if len(body) == 0:
      print("no movie recommendations found...")
      return
    # print recommendations
    print("Movie recommendations based on your reviews:")
    print(body)
    print(type(body))
    return

  except Exception as e:
    logging.error("**ERROR: get_rec() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return


###########################################################

# get graphs

def get_graphs(baseurl):
  """
  Prompts user for userid, connects to RDS, downloads two graphs to user's local current directory displaying overviews of genres they reviewed

  Parameters
  ----------
  none

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    userid=input("Please enter userid: ")
    api='/graphs/'+userid
    url = baseurl + api
    res=web_service_get(url)
    # let's look at what we got back:
  
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("Failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500 or res.status_code>= 400:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return
    
    body=res.json()
    print(body)
    if len(body) == 0:
      print("unable to get information for graphs...")
      return
    lengths=body[0]
    averages = body[1]
    firstname = body[2]
    num_reviews = body[3]
    
    print("Hello",firstname.title(),"you reviewed",num_reviews,"movie(s), loading your ratings per genre...")
    plt.pie(lengths.values(),labels=lengths.keys(),autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title("Movie Genres Watched by "+firstname)
    plt.savefig('genres_watched'+userid+'.pdf',format='pdf')
    plt.close()

    
    # barplot of genres
    plt.figure(figsize=(14, 10))
    plt.ylim(0, 10)
    plt.bar(averages.keys(),averages.values())
    plt.xlabel("Genres")
    plt.xticks(rotation=45)

    plt.ylabel("Average Rating")
    plt.title("Average Rating across Genres for "+firstname)
    # plt.show()
      # save plot
    plt.savefig('ratings_per_genre'+userid+'.pdf',format='pdf')
    
    plt.tight_layout()
    plt.close()
    print("**DONE**")
    return"Created and downloaded graphs"

  except Exception as e:
    logging.error("**ERROR: get_graphs() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
def find_userid():
  try:
    firstname=input("Please enter your first name(case sensitive to what you entered when writing a review): ")
    lastname=input("Please enter your last name(case sensitive to what you entered when writing a review): ")

    print("**setting up aws config**")
    # setup AWS based on config
    config_file = "moviereviews-config.ini"
    os.environ['AWS_SHARED_CREDENTIALS_FILE']=config_file
    
    configur = ConfigParser()
    configur.read(config_file)

    # configure for RDS access
    rds_endpoint = configur.get('rds','endpoint')
    rds_portnum = int(configur.get('rds','port_number'))
    rds_username = configur.get('rds','user_name')
    rds_pwd = configur.get('rds','user_pwd')
    rds_dbname = configur.get('rds','db_name')
    
    # open connection to the database
    print("**Opening connection to db**")
    # get dbConn
    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    
    print("**Retrieving user id**")

    sql="select userid from users where firstname = %s and lastname = %s;"
    user_row = datatier.retrieve_one_row(dbConn,sql,[firstname,lastname])
    
    # if no user found with userid, error
    if user_row == None or len(user_row) == 0:
        # print("No user found with userid",userid)
        print("No user found with name "+firstname+" "+lastname)
        return
    
    userid = user_row[0]
    print("your userid is "+str(userid))
    return
  except Exception as e:
    logging.error("**ERROR: get_userid() failed:")
    logging.error(e)
    return
  
############################################################
# main
#
try:
  print('** Welcome to MovieReviewsApp **')
  print()

  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  #
  # what config file should we use for this session?
  #
  config_file = 'moviereviews-config.ini'

  print("Config file to use for this session?")
  print("Press ENTER to use default, or")
  print("enter config file name>")
  s = input()

  if s == "":  # use default
    pass  # already set
  else:
    config_file = s

  #
  # does config file exist?
  #
  if not pathlib.Path(config_file).is_file():
    print("**ERROR: config file '", config_file, "' does not exist, exiting")
    sys.exit(0)


  #
  # setup base URL to web service:
  #
  configur = ConfigParser()
  configur.read(config_file)
  baseurl = configur.get('client', 'webservice')

  #
  # make sure baseurl does not end with /, if so remove:
  #
  if len(baseurl) < 16:
    print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
    sys.exit(0)

  if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
    print("**ERROR: update config file with your gateway endpoint")
    sys.exit(0)

  if baseurl.startswith("http:"):
    print("**ERROR: your URL starts with 'http', it should start with 'https'")
    sys.exit(0)

  lastchar = baseurl[len(baseurl) - 1]
  if lastchar == "/":
    baseurl = baseurl[:-1]

  # main processing loop:
  #
  cmd = prompt()

  while cmd != 0:
    #
    if cmd == 1:
      add_review(baseurl)
    elif cmd == 2:
      get_rec(baseurl)
    elif cmd == 3:
      get_graphs(baseurl)
    elif cmd == 4:
      find_userid()
    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** done **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
  
