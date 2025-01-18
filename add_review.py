import json
import boto3
import os
import datatier
import heapq
import requests
import find_movie

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
      
    #
    # setup AWS based on config file:
    #
      config_file = 'moviereviews-config.ini'
      os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
      configur = ConfigParser()
      configur.read(config_file)
    
    #
    # configure for RDS access
    #
      rds_endpoint = configur.get('rds', 'endpoint')
      rds_portnum = int(configur.get('rds', 'port_number'))
      rds_username = configur.get('rds', 'user_name')
      rds_pwd = configur.get('rds', 'user_pwd')
      rds_dbname = configur.get('rds', 'db_name')

      if "body" in event:
        print("HERE")
        body = json.loads(event["body"])
        items = ["firstname", "lastname", "moviename", "rating", "review"]
        mappings = {}
        for item in items:
            if item in body:
              mappings[item] = body[item]
            else:
               raise Exception("Missing item from event: ", item)
      
        # userid = mappings.get("userid")
        moviename = mappings.get("moviename")
        rating = mappings.get("rating")
        review = mappings.get("review")
        firstname = mappings.get("firstname")
        lastname = mappings.get("lastname")


      movie_data = find_movie.find_movie(moviename)
      if movie_data['statusCode'] == 400:
        return {
         'statusCode': 400,
         'body': json.dumps("No such movie..")
      }
      body = movie_data['body']
        
  
      data = json.loads(body)
    
      genres = data['genres']  
        
      dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
      cursor = dbConn.cursor()

      sql = "SELECT userid FROM users WHERE firstname = %s AND lastname=%s"
      parameters = [firstname, lastname]

      cursor.execute(sql, parameters)
      userid = cursor.fetchone()
      if userid is None:
        sql = """
            INSERT INTO users (lastname, firstname)
            VALUES (%s, %s);
        """
        parameters = [lastname, firstname]
        cursor.execute(sql, parameters)
        userid = cursor.lastrowid
        

      # Find every review submitted by the user
      sql = """
          INSERT INTO reviews (userid, moviename, rating, review, genre) 
          VALUES (%s, %s, %s, %s, %s)
          ON DUPLICATE KEY UPDATE 
            rating = VALUES(rating),
            review = VALUES(review),
            genre = VALUES(genre);
      """
      parameters = [userid, moviename, rating, review, genres]
      cursor.execute(sql, parameters)
      dbConn.commit()
      return {
         'statusCode': 200,
         'body': json.dumps("Review added successfully")
      }

  except Exception as err:
    print("**ERROR**")
    print(str(err))
    return {
      'statusCode': 500,
      'body': str(err)
    }