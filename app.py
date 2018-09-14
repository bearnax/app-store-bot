import os

from flask import Flask, jsonify, request
import requests
import psycopg2





# verification_token = os.environ['VERIFICATION_TOKEN']
app = Flask(__name__)

app_ids = (711074743, 418075935, 1098201243)

base_apple_url = "https://itunes.apple.com/lookup?id="



def request_data_from_apple(url, args):
    """ retrieve app data from apple

    Params:
        base_apple_url:type(string)
        args:type(int) > must be valid 10 digit app ids
    """

    search_url = url

    for arg in args:
        search_url += str(arg)
        search_url += ","

    return requests.get(search_url)





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
    r = request_data_from_apple(base_apple_url, app_ids)
    print(r)

    r_json = r.json()
    print(r_json['resultCount'])

    for i in r_json['results']:
        print(i["trackCensoredName"])
