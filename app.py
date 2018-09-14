import os

from flask import Flask, jsonify, request
import requests
import psycopg2
import play_scraper



# verification_token = os.environ['VERIFICATION_TOKEN']
app = Flask(__name__)
apple_ids = (711074743, 418075935, 1098201243)
google_names = ('com.catchsports.catchsports', 'com.foxsports.videogo')
# TODO: move app ids to database
base_apple_url = "https://itunes.apple.com/lookup?id="


def connect():
    """ Connect to PostgreSQL server """

    try:
        #retrieve params from environment
        env_host = os.environ['PG_HOST']
        env_database = os.environ['PG_DATABASE']
        env_user = os.environ['PG_USER']
        env_password = os.environ['PG_PASSWORD']

        return psycopg2.connect(
            host = env_host,
            dbname = env_database,
            user = env_user,
            password = env_password
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

    return requests.get(search_url)


def request_data_from_google(args):
    """ Retrieve app data from the Google Play Store via the
    play_scraper from pypi

    Params:
        args:type(str) > must be valid google package name
    """

    all_responses = []

    for arg in args:
        response = play_scraper.details(arg)
        parsed_response = [
            {'title': response['title']},
            {'category': response['category']},
            {'score': response['score']},
            {'score_histogram': response['histogram']},
            {'review_count': response['reviews']},
            {'last_updated': response['updated']},
            {'installs': response['installs']},
            {'current_version': response['current_version']},
            {'package_name': response['app_id']},
            {'required_android_version': response['required_android_version']}
        ]

        all_responses.append(parsed_response)

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

    r = request_data_from_google(google_names)
    print(r)
