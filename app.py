import os
import requests
import psycopg2
import play_scraper
import datetime

from flask import Flask, jsonify, request


# verification_token = os.environ['VERIFICATION_TOKEN']
app = Flask(__name__)
apple_ids = (
    711074743,
    418075935,
    1098201243
    )
google_names = (
    'com.catchsports.catchsports',
    'com.foxsports.videogo',
    'com.bleacherreport.android.teamstream'
    )
# TODO: move app ids to database
base_apple_url = "https://itunes.apple.com/lookup?id="



class Response(object):
    """docstring for AppleResponse"""
    __slots__=['title', 'category', 'average_rating','review_count',
        'last_updated', 'installs', 'current_version', 'package_name',
        'minimum_os_version', 'average_rating_current_version',
        'review_count_current_version', 'apple_app_id']

    def __init__(self, title, category, average_rating, review_count,
        last_updated, installs, current_version, package_name,
        minimum_os_version, average_rating_current_version,
        review_count_current_version, apple_app_id):

        self.title = title
        self.category = category
        self.average_rating = average_rating
        self.review_count = review_count
        self.last_updated = last_updated
        self.installs = installs
        self.current_version = current_version
        self.package_name = package_name
        self.minimum_os_version = minimum_os_version
        self.average_rating_current_version = average_rating_current_version
        self.review_count_current_version = review_count_current_version
        self.apple_app_id = apple_app_id

    def lower_category_case(self):
        self.category = self.category.lower()

    def strip_apple_update_date(self):
        self.last_updated = datetime.datetime.strptime(
            self.last_updated, '%Y-%m-%dT%H:%M:%SZ').date()

    def strip_android_update_date(self):
        self.last_updated = datetime.datetime.strptime(
            self.last_updated, '%B %d, %Y').date()


def connect():
    """ Connect to PostgreSQL server """

    try:
        # retrieve params from environment
        env_host = os.environ['PG_HOST']
        env_database = os.environ['PG_DATABASE']
        env_user = os.environ['PG_USER']
        env_password = os.environ['PG_PASSWORD']

        return psycopg2.connect(
            host=env_host,
            dbname=env_database,
            user=env_user,
            password=env_password
        )
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


def get_sql_data(query, *args):
    """ retrieve data from the postgresql database """

    try:
        assert query.count('%s') == len(args)

        conn = connect()
        cursor = conn.cursor()
        cursor.execute(query, args)
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        # print("SUCCESS: get_sql_data")

        return data

    except AssertionError:
        print("ERROR: get_sql_data(), wrong number of arguments")


def post_sql_data(query, *args):
    """ insert data into the postgresql database
        This function can be used to post new data or delete data

        Post / Delete should be indicated in the db query

    """

    try:
        assert query.count('%s') == len(args)

        conn = connect()
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        cursor.close()
        conn.close()

        # print("SUCCESS: post_sql_data")

    except AssertionError:
        print("ERROR: post_sql_data(), wrong number of arguments")


# TODO: add database queries


def request_data_from_apple(url, args):
    """ Retrieve app data from the Apple App Atore via
    the Apple App Store url (api) call

    Params:
        url:type(string) > must be apple store api url + '?id=' arg
        args:type(int) > must be valid 10 digit app ids
    """

    search_url = url

    for arg in args:
        search_url += str(arg)
        search_url += ","

    try:
        r = requests.get(search_url)
        data = r.json()
        return data

    except TypeError as error:
        print(error)



def parse_data_from_apple(data):

    all_responses = []

    for result in data['results']:

        response = Response(
            title=result['trackName'],
            category=result['primaryGenreName'],
            average_rating=result['averageUserRating'],
            review_count=result['userRatingCount'],
            last_updated=result['currentVersionReleaseDate'],
            installs=None,
            current_version=result['version'],
            package_name=None,
            minimum_os_version=result['minimumOsVersion'],
            average_rating_current_version=result[
                'averageUserRatingForCurrentVersion'],
            review_count_current_version=result[
                'userRatingCountForCurrentVersion'],
            apple_app_id=result['trackId'],
        )

        # normalize non-uniform variables
        response.strip_apple_update_date()
        response.lower_category_case()

        all_responses.append(response)

    return all_responses



def request_data_from_google(args):
    """ Retrieve app data from the Google Play Store via the
    play_scraper from pypi

    Params:
        args:type(str) > must be valid google package name
    """

    all_responses = []

    for arg in args:

        raw_response = play_scraper.details(arg)

        response = Response(
            title=raw_response['title'],
            category=raw_response['category'][0],
            average_rating=raw_response['score'],
            review_count=raw_response['reviews'],
            last_updated=raw_response['updated'],
            installs=raw_response['installs'],
            current_version=raw_response['current_version'],
            package_name=raw_response['app_id'],
            minimum_os_version=raw_response['required_android_version'],
            average_rating_current_version=None,
            review_count_current_version=None,
            apple_app_id=None,
        )

        # normalize non-uniform variables
        response.strip_android_update_date()
        response.lower_category_case()

        all_responses.append(response)

    return all_responses


@app.route('/app-bot', methods=['POST'])
def app_bot():
    if request.form['token'] == verification_token:

        data = request.values
        command = data['text'].lower()

        if command == "manual data refresh":
            """ initiate data ingestion manually
            """
            # TODO: write some code here please
            pass

        elif command == 'add_new app':
            """ initiate data ingestion manually
            """
            # TODO: write some code here please, this one probaby needs 'banter'
            pass

        elif command == 'hide app from ranking':
            """ initiate data ingestion manually
            """
            # TODO: write some code here please, this one probaby needs 'banter'
            pass

        elif command == 'delete app':
            """ initiate data ingestion manually
            """
            # TODO: write some code here please, this one probaby needs 'banter'
            pass

        elif command == 'rank today':
            """ initiate data ingestion manually
            """
            # TODO: write some code here please
            pass

        elif command == 'rank current version':
            """ initiate data ingestion manually
            """
            # TODO: write some code here please
            pass

        else:
            bot_response = {
                'response_type': 'in_channel',
                'attachments': [
                    {
                        'title': 'error: unknown command',
                        'text': 'imma pray on this one.'
                    }
                ]
            }

        return jsonify(bot_response)


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }

    error_response = jsonify(message)
    error_response.status_code = 404

    return error_response


if __name__ == '__main__':
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host='0.0.0.0', port=port, debug=True)

    google_response = request_data_from_google(google_names)
    for i in google_response:
        print("{} where package_name={}\n   avg_rating={}".format(
            i.title,
            i.package_name,
            i.average_rating
        ))

    apple_response = request_data_from_apple(base_apple_url, apple_ids)
    parsed_apple_responses = parse_data_from_apple(apple_response)
    for i in parsed_apple_responses:
        print("{} where app_id={}\n   avg_rating={}".format(
            i.title,
            i.apple_app_id,
            i.average_rating
        ))
