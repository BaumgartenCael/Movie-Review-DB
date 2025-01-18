import json
import boto3
import os
import requests

def find_movie(moviename):
    try:
        print("**STARTING**")
        print("**lambda: api_data**")

        print("**Accessing request body**")

        url = "https://api.themoviedb.org/3/search/movie?query={0}&include_adult=false&language=en-US&page=1".format(moviename)
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5MWEyZmZlZDhkNzk5OGM4MWZmNzRhNzI3MWY2YjQxYyIsIm5iZiI6MTczMzQ0MDg2OC4yMDk5OTk4LCJzdWIiOiI2NzUyMzU2NDgwMmJhZDE2MDkxYWEwMTQiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.vIDSDPG21h1FoxtY13Wm204yz_VcGvAPpgNJ-hXCI-w"
        }
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        if len(data["results"]) == 0:
            print("no such movie...")
            return {
                'statusCode': 400,
                'body': json.dumps("no such movie...")
            }
        moviedata = data["results"][0]
        genreids = moviedata["genre_ids"]
        print ("Found movie:", moviedata["title"])

        url = "https://api.themoviedb.org/3/genre/movie/list?language=en"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5MWEyZmZlZDhkNzk5OGM4MWZmNzRhNzI3MWY2YjQxYyIsIm5iZiI6MTczMzQ0MDg2OC4yMDk5OTk4LCJzdWIiOiI2NzUyMzU2NDgwMmJhZDE2MDkxYWEwMTQiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.vIDSDPG21h1FoxtY13Wm204yz_VcGvAPpgNJ-hXCI-w"
        }
        response = requests.get(url, headers=headers)
        data2 = json.loads(response.text)
        genrelist = ""
        for g in data2["genres"]:
            if g["id"] in genreids:
                if genrelist != "":
                    genrelist += ","
                genrelist += g["name"]
        
        print("**DONE, returning data**")
        data3 = {
            "genres" : genrelist,
            "rating" : moviedata["vote_average"]
        }
        print("HERE!")

        return {
            'statusCode': 200,
            'body': json.dumps(data3)
        }

    except Exception as err:
        print("**ERROR**")
        print(str(err))
        return {
            'statusCode': 500,
            'body': json.dumps(str(err))
        }

#print(lambda_handler({"body" : "{\"moviename\" : \"The Godfather\"}"}, ""))