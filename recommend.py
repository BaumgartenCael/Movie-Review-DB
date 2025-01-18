import json
import boto3
import os
import datatier
import heapq
import requests

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

    # get userid from event: could be a parameter or could be part of URL path ("pathParameters"):


    if "pathParameters" in event:
        if "userid" in event["pathParameters"]:
            userid = event["pathParameters"]["userid"]
        else:
            raise Exception("requires userid parameter in pathParameters")

    if not userid:
        raise Exception("requires userid parameter in event")

    dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
    cursor = dbConn.cursor()

    # Find every review submitted by the user
    sql = "SELECT * FROM reviews WHERE userid = %s"
    parameters = [userid]
    cursor.execute(sql, parameters)
    all_reviews = cursor.fetchall()

    TMDB_API_KEY = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5MWEyZmZlZDhkNzk5OGM4MWZmNzRhNzI3MWY2YjQxYyIsIm5iZiI6MTczMzQ0MDg2OC4yMDk5OTk4LCJzdWIiOiI2NzUyMzU2NDgwMmJhZDE2MDkxYWEwMTQiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.vIDSDPG21h1FoxtY13Wm204yz_VcGvAPpgNJ-hXCI-w'
    TMDB_BASE_URL = 'https://api.themoviedb.org/3' 
    headers = {
      "accept": "application/json",
      "Authorization": f"Bearer {TMDB_API_KEY}"
    }


    #
    # Evaluate the movies this user has seen. Rank their preferences based on ratings for movies of certain genres.
    #

    movies_seen = [] # Track movies to make sure we do not recommend movies the user has already seen
    genre_prefs = {} # Dictionary mapping genres to numeric values indicating preference toward that genre

    # A review importantly contains the movie name, the rating, and the genres of the movie
    for review in all_reviews:
      rating = review[3]
      movies_seen.append(review[2])
      genres = review[5].split(',') # May need to change this later depending on formatting for genres
  
      # Calculate the preference for each genre 
      for genre in genres:
          normalization = len(genres) 
          score = (rating - 4) / normalization
          if genre in genre_prefs:
            genre_prefs[genre] += score
          else:
            genre_prefs[genre] = score# + 0.2 # Add flat amount for watching the genre at all

    # Now that we have calculated genre preferences, we need to get the id of the favorite genre
    favorite_genre, score = max(genre_prefs.items(), key=lambda item: item[1])

    url = f"{TMDB_BASE_URL}/genre/movie/list?api_key={TMDB_API_KEY}&language=en-US"
    # headers = {
    #   "accept": "application/json",
    #   "Authorization": f"Bearer {TMDB_API_KEY}"
    # }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    genres = response.json().get('genres', [])
    genre_map = {genre['name']: genre['id'] for genre in genres}
    favorite_genre_id = genre_map.get(favorite_genre)
    

    # We have the genre id, now we return a list of movies that contain that genre
    url = f"{TMDB_BASE_URL}/discover/movie"
    params = {
      'api_key': TMDB_API_KEY,
      'with_genres': favorite_genre_id,
      'sort_by': 'popularity.desc',
      'language': 'en-US',
    }

    response = requests.get(url,headers=headers, params=params)
    response.raise_for_status()
    movies = response.json().get('results', [])
    movie_list = [(movie['title'], movie['vote_average'], movie['genre_ids']) for movie in movies]

    #
    # Now that we have evaluated preferences from the user, let's find movies that match those preferences
    #
    recs = []
    url = f"{TMDB_BASE_URL}/genre/movie/list"
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses
    genres = response.json().get('genres', [])
    genre_mapping = {genre['id']: genre['name'] for genre in genres}
    for movie in movie_list:
      title = movie[0]
      rating = movie[1]
      genre_ids = movie[2]
      total_score = 0
      rec_number = 3
      genre_names = [genre_mapping.get(genre_id, "Unknown") for genre_id in genre_ids]

      # Skip movies we've seen
      if title in movies_seen:
          continue
      
      # Add to score based on user's genre preference per genre in the movie.
      for genre in genre_names:
          if genre not in genre_prefs:
            genre_score = 0
          else:
            genre_score = genre_prefs[genre]
          total_score += genre_score

      # Normalize the score to get the average genre rank and prefer higher rated movies
      total_score /= len(genres)
      total_score *= rating
      heapq.heappush(recs, (-total_score, title))
    final_recs = []


    for i in range(0, rec_number):
        value, item = heapq.heappop(recs)
        final_recs.append(item)
    return {
      'statusCode': 200,
      'body': json.dumps(final_recs)
    }
    


  except Exception as err:
    print("**ERROR**")
    print(str(err))
    return {
      'statusCode': 500,
      'body': str(err)
    }