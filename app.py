import os
import requests
import psycopg2
import play_scraper
import datetime
from slackclient import SlackClient

from flask import Flask, jsonify, request, make_response





APP = Flask(__name__)

SLACK_TOKEN = os.environ.get('VERIFICATION_TOKEN', True)
SLACK_CLIENT = SlackClient(SLACK_TOKEN),

SLACK_OATH = os.environ.get('SLACK_OATH_TOKEN', True)
SLACK_API_CLIENT = SlackClient(SLACK_OATH)




class Error(Exception):
    """Base class for exceptions"""
    pass

class NoCommandReceivedError(Error):
    """Raised when no command is recieved from slack user"""
    __slots__=['error_message']
    def __init__(self):
        self.error_message = "No command received, stop bothering me for no reason."


class NoAvailableCommandError(Error):
    """Raised when a command is received from the slack user,
    but the command is misunderstood and cannot be performed.
    """

    __slots__=['error_message']

    def __init__(self):
        self.error_message = "I think you want some help, but I can't understand what you want."




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

def get_channel_info(channel_id):
    call_response = SLACK_API_CLIENT.api_call(
        "channels.info",
        channel=channel_id
    )

    try:
        call_response['ok']
        return call_response['channel']

    except Exception as error:
        print("Error in get_channels_info | error_message:{}".format(
            call_response['error']
        ))
        return []

def get_channels():
    call_response = SLACK_API_CLIENT.api_call("channels.list")

    try:
        call_response['ok']
        return call_response['channels']

    except Exception as error:
        print("Error in get_channels | error_message:{}".format(
            call_response['error']
        ))
        return []

def print_channels():
    channels = get_channels()

    if channels == None:
        pass

    print("Available Channels: ")
    for channel in channels:
        channel_info = get_channel_info(channel['id'])

        print("   {} id=({})\n      most recent change:{}".format(
            channel['name'],
            channel['id'],
            channel_info['latest']['text']
        ))



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


def storebot_do(incoming_payload):
    data = incoming_payload.json
    print(data)
    text = data['event']['text']
    print(text)
    user_name = data['authed_users'][0]
    print(user_name)
    command = remove_user_name(user_name, text).lower()
    print(command)
    print(len(command))
    channel_id = data['event']['channel']

    try:
        if len(command) == 0:
            raise NoCommandReceivedError

        elif 'do' not in command[0:2]:
            raise NoAvailableCommandError

        else:
            message = "Your wish is my command :crystal_ball:"

    except NoCommandReceivedError as error:
        message = error.error_message

    except NoAvailableCommandError as error:
        message = error.error_message

    send_slack_message(channel_id, message)


@APP.route('/mentions', methods=['POST'])
def mentions():

    return make_response(
        "Mention received", 200,
    ), storebot_do(request)





if __name__ == '__main__':
    print('')

    # slack_connection_test()
    # print_channels()
    # send_slack_message('CCPQ8EV4J', 'bonjour le monde')

    port = int(os.environ.get("PORT", 5000))
    APP.run(host='0.0.0.0', port=port, debug=True)


    print('')

# https://22b4974e.ngrok.io/mentions












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



# def request_response(url, command_received):
#     headers = {'content-type': 'application/json'}
#     text = {
#         'title': "Keepin' it 200",
#         'text': "Your command ({}) was recieved. I'll let you know when I'm done working on it".format(command_received)
#     }
#     payload = jsonify(text)
#
#     requests.post(url, headers=headers, data=payload)

def verify_url_with_slack(request_load):
    try:
        request_load.json['token'] == SLACK_TOKEN

        payload = {
            "challenge": "{}".format(request_load.json['challenge'])
        }

        return jsonify(payload)

    except Exception as error:
        print(error)



def slack_api_message_response():
    """ respond to a user / channel via the slack api
    """

    # do stuff

    pass





# @app.route('/mentions', methods=['POST'])
# def mentions():
#     print(request)
#
#     payload = {
#         'response_type': 'in_channel',
#         "text": "no hablo ingles"
#     }
#
#     return jsonify(payload)



# @app.route('/storebot', methods=['POST'])
# def storebot():
#     if request.form['token'] == SLACK_TOKEN:
#
#         data = request.values
#         command = data['text'].lower()
#         response_url = data['response_url']
#         request_response(response_url, command)
#
#         payload = (
#             {
#                 'response_type': 'in_channel',
#                 'text': '{} & {}'.format(command, response_url)
#             }
#         )

        # if command == "manual data refresh":
        #     """ initiate data ingestion manually
        #     """
        #     # Quickly respond to make slack happy, then, toil
        #     request_response(data['response_url'], command)
        #
        #     apple_ids = get_sql_data(GET_ALL_APPLE_IDS)
        #     google_ids = get_sql_data(GET_ALL_GOOGLE_IDS)
        #
        #     apple_response = request_data_from_apple(BASE_APPLE_URL, apple_ids)
        #     parsed_apple_response = parse_data_from_apple(apple_response)
        #     google_responses = request_data_from_google(google_ids)
        #
        #     all_responses = []
        #
        #     for i in parsed_apple_response:
        #         all_responses.append(i)
        #
        #     for i in google_responses:
        #         all_responses.append(i)
        #
        #     insertion_success_counter = 0
        #     insertion_error_counter = 0
        #     error_messages = []
        #
        #     for i in all_responses:
        #         try:
        #             post_sql_data(INSERT_APP_DATA,
        #                 i.title,
        #                 i.category,
        #                 i.average_rating,
        #                 i.review_count,
        #                 i.last_updated,
        #                 i.installs,
        #                 i.current_version,
        #                 i.package_name,
        #                 i.minimum_os_version,
        #                 i.average_rating_current_version,
        #                 i.review_count_current_version,
        #                 i.apple_app_id
        #             )
        #             insertion_success_counter += 1
        #
        #         except Exception as error:
        #             print(error)
        #             insertion_error_counter += 1
        #             error_messages.append(str(error))
        #
        #     if insertion_error_counter == 0:
        #         bot_response = {
        #             'response_type': 'in_channel',
        #             'pre-text': '{} records added, with 0 errors'.format(
        #                 insertion_success_counter
        #             )
        #         }
        #     else:
        #         bot_response = {
        #             'response_type': 'in_channel',
        #             'pre-text': '{} records added, with {} errors'.format(
        #                 insertion_success_counter,
        #                 insertion_error_counter
        #             ),
        #             'text': 'error messages: {}'.format(
        #                 error_messages
        #             )
        #         }
        #
        # elif command == 'test':
        #     request_response(data['response_url'], command)
        #     bot_response = {
        #         'response_type': 'in_channel',
        #         'text': 'the full response'
        #     }
        #
        # elif command == 'get ranking':
        #     """ return the all time ranking for all tracked apps
        #     """
        #     bot_response = {
        #         'response_type': 'in_channel',
        #         'attachments': [
        #             {
        #                 'title': 'request received',
        #                 'text': 'response sent'
        #             }
        #         ]
        #     }
        #
        # elif command == 'rank current version':
        #     """ initiate data ingestion manually
        #     """
        #     # TODO: write some code here please
        #     pass
        #
        # else:
        #     bot_response = {
        #         'response_type': 'in_channel',
        #         'attachments': [
        #             {
        #                 'title': 'error: unknown command',
        #                 'text': 'imma pray on this one.'
        #             }
        #         ]
        #     }

        # return jsonify(payload)


# @app.errorhandler(404)
# def not_found(error=None):
#     message = {
#         'status': 404,
#         'message': 'Not Found: ' + request.url,
#     }
#
#     error_response = jsonify(message)
#     error_response.status_code = 404
#
#     return error_response
#
#
# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host='0.0.0.0', port=port, debug=True)

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
