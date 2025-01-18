# Movie-Review-DB
Class final project for a serverless AWS RDS that recommends movies to users based on their submitted movie reviews.

Utilizes a database called movie-reviews-310. Main.py is the "client side", making calls to lambda functions contained on AWS. The files make_graphs, add_review, and recommend contain the code for the lambda functions but are not required to run the main.py file. 

To use it, just fill in the access key variables in the config-template.ini file.
