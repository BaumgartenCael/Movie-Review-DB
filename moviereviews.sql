CREATE DATABASE moviereviews;

USE moviereviews;

DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS users;

CREATE TABLE users
(
    userid       int not null AUTO_INCREMENT,
    lastname     varchar(64) not null,
    firstname    varchar(64) not null,
    PRIMARY KEY (userid)
);


ALTER TABLE users AUTO_INCREMENT = 80001;  -- starting value


CREATE TABLE reviews
(
    reviewid    int not null AUTO_INCREMENT,
    userid       int not null,
	moviename   varchar(128),
    rating       int not null,
    review      varchar(128) not null,
    genre        varchar(64) not null,
    PRIMARY KEY (reviewid),
    FOREIGN KEY (userid) REFERENCES users(userid)
);


ALTER TABLE reviews AUTO_INCREMENT = 1001;  -- starting value
ALTER TABLE reviews
ADD CONSTRAINT unique_review UNIQUE (userid, moviename);

CREATE USER 'user310'@'%' IDENTIFIED BY 'icupdawg';
GRANT ALL PRIVILEGES ON moviereviews.* TO 'user310'@'%';
