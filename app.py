import os
import requests
import psycopg2
import play_scraper
import datetime
from slackclient import SlackClient

from flask import Flask, jsonify, request, make_response



# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++ CONSTANTS

APP = Flask(__name__)

SLACK_TOKEN = os.environ.get('VERIFICATION_TOKEN', True)
SLACK_CLIENT = SlackClient(SLACK_TOKEN),

SLACK_OATH = os.environ.get('SLACK_OATH_TOKEN', True)
SLACK_API_CLIENT = SlackClient(SLACK_OATH)

BASE_APPLE_URL = "https://itunes.apple.com/lookup?id="


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++ CLASSES

class Error(Exception):
    """Base class for exceptions"""
    pass

class NoCommandReceivedError(Error):
    """Raised when no command is recieved from slack user"""
    __slots__=['error_message']
    def __init__(self):
        self.error_message = "No command received, stop bothering me for no reason."


class NotACommandError(Error):
    """Raised when a command is received from the slack user,
    but the command is misunderstood and cannot be performed.
    """

    __slots__=['error_message']

    def __init__(self):
        self.error_message = "I'm afraid I can't do that :space_invader:"

class SlackRequest(object):
    """docstring for SlackRequest"""
    __slots__=['data', 'text', 'user_name', 'command', 'channel_id', 'event_id']

    def __init__(self, data):

        self.data = data
        self.text = self.data['event']['text']
        self.user_name = data['authed_users'][0]
        self.command = remove_user_name(
            self.slack_user_name,
            self.text).lower()
        self.channel_id = self.data['event']['channel']
        self.event_id = data['event_id']

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

class EventLog(object):
    """docstring for event log"""
    __slots__=['event_log']

    def __init__(self):
        self.event_log = []

    def event_log_length(self):
        return len(self.event_log)

    def shorten_log(self, length_to_remove):
        del self.event_log[0:length_to_remove]

    def delete_all_logs(self):
        self.event_log.clear()


# +++++++++++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++ SLACK FUNCTIONS
# +++++++++++


def slack_connection_test():
    print('CONNECTING...')
    try:
        test = SLACK_API_CLIENT.api_call('api.test')
        auth = SLACK_API_CLIENT.api_call('auth.test')

        assert test['ok']
        assert auth['ok']

        print('Connection Success!\n')

    except Exception as error:
        print("Conncetion Failed:")
        print(error)

def verify_url_with_slack(request_load):
    try:
        request_load.json['token'] == SLACK_TOKEN

        payload = {
            "Content-type": "application/json",
            "challenge": "{}".format(request_load.json['challenge'])
        }

        return jsonify(payload)

    except Exception as error:
        print(error)

def parse_mention(incoming_payload):
    data = incoming_payload.json

    print('{}: {}'.format(
        data['event']['type'],
        data['event']['text']
    ))


def send_slack_message(channel_id, message):
    """
    params: (
        channel_id :: type(str)
        message :: type(str)
    )
    """
    SLACK_API_CLIENT.api_call(
        'chat.postMessage',
        channel=channel_id,
        text=message
    )



def strip_decorators(name):
    strp_name = name.strip('<>@')
    return strp_name


def remove_user_name(slack_user_name, string):
    """ Strip out user name from a slack mention text
    """
    user_name = strip_decorators(slack_user_name)

    try:
        assert user_name in string
        command = strip_decorators(string.replace(slack_user_name, ''))
        return command.lstrip()

    except AssertionError:
        return string


def connect():
    """ Connect to PostgreSQL server """

    try:
        # retrieve params from environment
        env_host = os.environ.get('PG_HOST', True)
        env_database = os.environ.get('PG_DATABASE', True)
        env_user = os.environ.get('PG_USER', True)
        env_password = os.environ.get('PG_PASSWORD', True)

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
    FROM tracked_apps;
"""

GET_ALL_GOOGLE_IDS = """
    SELECT google_name
    FROM tracked_apps;
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
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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
        search_url += str(arg[0])
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

        raw_response = play_scraper.details(arg[0])

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




def refresh_data():
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
                i.average_rating,
                i.review_count,
                i.last_updated,
                i.installs,
                i.current_version,
                i.package_name,
                i.minimum_os_version,
                i.average_rating_current_version,
                i.review_count_current_version,
                i.apple_app_id
            )
            insertion_success_counter += 1

        except Exception as error:
            print(error)
            insertion_error_counter += 1
            error_messages.append(str(error))

    if insertion_error_counter == 0:
        message = '{} records added, with 0 errors'.format(
                insertion_success_counter
        )

    else:
        message = '{} records added, with {} errors'.format(
                insertion_success_counter,
                insertion_error_counter
            )

    return message



def storebot_do(incoming_payload):
    """delayed response to the slack client
    """

    #parse the incoming_payload
    request = SlackRequest(incoming_payload)

    #Verify the message isn't a duplicate
    if request.event_id in log:
        print("Error: status=429 Duplicate Request")
        return make_response(
            "Duplicate Request", 429,
        )
    else:
        log.append(request.event_id)



    try:
        if len(request.command) == 0:
            print('no text at all')
            raise NoCommandReceivedError

        elif 'do' not in request.command[0:2]:
            print('is not a command')
            raise NotACommandError

        elif 'manual refresh' in request.command:
            print('manual data refresh requested')
            message = refresh_data()

        else:
            print('do, something unknown')
            message = "Your wish is my command :crystal_ball:"

    except NoCommandReceivedError as error:
        message = error.error_message

    except NotACommandError as error:
        message = error.error_message

    send_slack_message(request.channel_id, message)


@APP.route('/mentions', methods=['POST'])
def mentions():
    # response = verify_url_with_slack(request)
    # return response
    # VERIFIED: https://ef07805a.ngrok.io/mentions

    return make_response(
        "Mention received", 200,
    ), storebot_do(request)

@APP.errorhandler(404)
# TODO: Create an exception and real errors for this
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }

    error_response = jsonify(message)
    error_response.status_code = 404

    return error_response





if __name__ == '__main__':
    print('STARTING')
    log = EventLog

    slack_connection_test()
    # send_slack_message('CCQBB1231', 'Bonjour le monde :tada:')

    port = int(os.environ.get("PORT", 5000))
    APP.run(host='0.0.0.0', port=port, debug=True)
