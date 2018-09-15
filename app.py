import os
import requests
import psycopg2
import play_scraper
import datetime

from flask import Flask, jsonify, request


verification_token = os.environ['VERIFICATION_TOKEN']
app = Flask(__name__)

BASE_APPLE_URL = "https://itunes.apple.com/lookup?id="



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


GET_ALL_APPLE_IDS = """
    SELECT apple_id
    FROM app_data;
"""

GET_ALL_GOOGLE_IDS = """
    SELECT google_name
    FROM app_data;
"""

INSERT_APP_DATA = """
    INSERT INTO app_data (
      title,
      category,
      average_user_rating,
      review_count,
      last_updated,
      installs,
      current_version,
      package_name,
      minimum_os_version,
      average_user_rating_current_version,
      review_count_current_version,
      apple_app_id
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""


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


@app.route('/storebot', methods=['POST'])
def storebot():
    if request.form['token'] == verification_token:

        data = request.values
        command = data['text'].lower()

        if command == "manual data refresh":
            """ initiate data ingestion manually
            """
            apple_ids = get_sql_data(GET_ALL_APPLE_IDS)
            google_ids = get_sql_data(GET_ALL_GOOGLE_IDS)

            apple_response = request_data_from_apple(BASE_APPLE_URL, apple_ids)
            parsed_apple_response = parse_data_from_apple(apple_response)
            google_responses = request_data_from_google(google_ids)

            all_responses = []

            for i in parsed_apple_response:
                all_responses.append(i)

            for i in google_responses:
                all_responses.append(i)

            insertion_success_counter = 0
            insertion_error_counter = 0
            error_messages = []

            for i in all_responses:
                try:
                    post_sql_data(INSERT_APP_DATA,
                        i.title,
                        i.category,
                        i.average_user_rating,
                        i.review_count,
                        i.last_updated,
                        i.current_version,
                        i.package_name,
                        i.minimum_os_version,
                        i.average_user_rating_current_version,
                        i.review_count_current_version,
                        i.apple_app_id
                    )
                    insertion_success_counter += 1
                except Exception as error:
                    insertion_error_counter += 1
                    error_messages.append(str(error))

            if insertion_error_counter == 0:
                bot_response = {
                    'response_type': 'in_channel',
                    'pre-text': '{} records added, with 0 errors'.format(
                        insertion_success_counter
                    )
                }
            else:
                bot_response = {
                    'response_type': 'in_channel',
                    'pre-text': '{} records added, with {} errors'.format(
                        insertion_success_counter,
                        insertion_error_counter
                    ),
                    'text': 'error messages: {}'.format(
                        error_messages
                    )
                }

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

        elif command == 'get ranking':
            """ return the all time ranking for all tracked apps
            """
            bot_response = {
                'response_type': 'in_channel',
                'attachments': [
                    {
                        'title': 'request received',
                        'text': 'response sent'
                    }
                ]
            }

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

    # google_response = request_data_from_google(google_names)
    # for i in google_response:
    #     print("{} where package_name={}\n   avg_rating={}".format(
    #         i.title,
    #         i.package_name,
    #         i.average_rating
    #     ))
    #
    # apple_response = request_data_from_apple(BASE_APPLE_URL, apple_ids)
    # parsed_apple_responses = parse_data_from_apple(apple_response)
    # for i in parsed_apple_responses:
    #     print("{} where app_id={}\n   avg_rating={}".format(
    #         i.title,
    #         i.apple_app_id,
    #         i.average_rating
    #     ))
