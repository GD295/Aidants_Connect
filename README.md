# Aidants Connect

Aidants Connect is an app that allows people who want to assist FranceConnect users to do so with full transparency.

[![CircleCI](https://circleci.com/gh/betagouv/Aidants_Connect/tree/master.svg?style=svg)](https://circleci.com/gh/betagouv/Aidants_Connect/tree/master)

## Stack
Django
PostgreSQL

## Environment
AidantConnect runs on Python 3.7

# How to setup the Database

Install PostgreSQL (for Mac OSX)
```
brew install postgresql
brew services start postgresql
createdb `whoami`
```

Create the database
```
psql
```
In the postgreSQL prompt
``` 
CREATE USER aidants_connect_team;
CREATE DATABASE aidants_connect OWNER aidants_connect_team;
ALTER USER aidants_connect_team CREATEDB;
```

## How to install the app

Use a virtual environment in your working directory

```
virtualenv venv
source venv/bin/activate
```

Install the dependencies

```
pip install -r requirements.txt
```

If you get `ld: library not found for -lssl` as an error message, try:
```
export LIBRARY_PATH=$LIBRARY_PATH:/usr/local/opt/openssl/lib/
```

Create a `.env` file at the root of the project with the following entries:
```
HOST= <insert_your_data> #e.g. http://localhost:8000

APP_SECRET=<insert_your_secret>

FC_CALLBACK_URL=<insert_your_data>

TEST="Everything is awesome"

DATABASE_NAME=aidants_connect
DATABASE_USER=aidants_connect_team
DATABASE_PASSWORD='' or <insert_your_data>
DATABASE_URL='' or <insert_your_data>
DATABASE_PORT='' or <insert_your_data>

FC_CLIENT_ID = <insert_your_data>
FC_CLIENT_SECRET= <insert_your_data>

FC_AS_FS_ID=<insert_your_data>
FC_AS_FS_SECRET=<insert_your_data>

# Optional
DATABASE_SSL
DEBUG
```

Create a `staticfiles` directory
```
mkdir staticfiles
```

Run the migrations
```
python manage.py makemigrations
python manage.py migrate
```

Create a superuser
```
python manage.py createsuperuser --username name 
```

## How to run the tests

```
flake8
python manage.py test
```
## How to run the app

To run the app on port 8000
```
python manage.py runserver 8000
```

## How to run the functional tests
Install [Gecko driver](https://github.com/mozilla/geckodriver/releases)

```
brew install geckodriver
```

## Test FranceConnect credentials
[here](https://github.com/france-connect/identity-provider-example/blob/master/database.csv)
