# import numpy as np
import json
import boto3
import os
import datatier
from configparser import ConfigParser
# Retrieves all reviews from reviews table correlating to userid and creates+displays a graph of most watched genre
def lambda_handler(event, context):
    try:
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
        # get userid from event: could be a parameter or could be part of URL path ("pathParameters"):
        # if "body" in event:
        #     body = json.loads(event["body"])
        #     if "userid" in body:
        #         userid = body["userid"]
        #     else:
        #         raise Exception("requires userid parameter in event")
        if "pathParameters" in event:
            if "userid" in event["pathParameters"]:
                userid = event["pathParameters"]["userid"]
            else:
                raise Exception("requires userid parameter in pathParameters")
        else:
            raise Exception("requires userid parameter in event")
         
        # open connection to the database
        print("**Opening connection to db**")
        # get dbConn
        dbConn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
        
        print("**Retrieving user reviews**")
    
        sql="select rating,genre from reviews where userid = %s;"
        rows = datatier.retrieve_all_rows(dbConn,sql,userid)
        sql2 = "select firstname from users where userid = %s ;"
        user_row = datatier.retrieve_one_row(dbConn,sql2,userid)
        
        # if no user found with userid, error
        if user_row == None or len(user_row) == 0:
            print("No user found with userid",userid)
            return{
            'statusCode':400,
            'body':json.dumps("No user found")
            }
        # if no reviews, return 
        if len(rows) == 0 or rows == None:
            print("No reviews found for {firstname}.")
            return{
            'statusCode':400,
            'body':json.dumps("No reviews found")
            }
        
        firstname = user_row[0]
        print("Hello",firstname.title(),"you reviewed",len(rows),"movie(s), loading your ratings per genre...")
        # dictionary of genres and list of star ratings

        genres = {}
        for row in rows:
            rating=row[0]
            genre_str = row[1]
            # turn string into list CHANGE THIS TO SPLIT ON COMMAS ONCE DB IS UPDATED
            user_genres = genre_str.split(",")
            for genre in user_genres:
                key = genres.get(genre)
                if key == None:
                    genres[genre]=[int(rating)]
                else:
                    genres[genre].append(int(rating))
            
        # create pie chart
        lengths = {key:len(value) for key,value in genres.items()}
        # plt.figure(figsize=(14,8))
        # num_colors = len(lengths.keys())
        # colors=plt.colormaps.get_cmap("Pastel2")(range(num_colors))
        

        averages={key:sum(value)/len(value) for key,value in genres.items()}
        print("**DONE**")
        # data={"genres watched":genres.keys()}
        return{
            'statusCode':200,
            'body':json.dumps([lengths,averages,firstname,len(rows)])
        }
    except Exception as err:
        print("*ERROR*")
        print(str(err))
        return {
        'statusCode': 500,
        'body': json.dumps({"error": str(err)})
    }