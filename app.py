from flask import Flask, request

from models.Languages import Languages
from utils import get_content, get_xml, response_content, get_archives, convert_to_original_files

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return '.-.'


@app.route('/api')
def api():
    return 'Welcome to the API!'


@app.route('/api/ping')
def ping():
    return 'pong'


@app.route('/api/generateUML', methods=['POST'])
def generateUML():
    url = request.json['url']

    # We get the languages from the request and we convert them to the Languages enum and get the value
    languages = request.json['languages']
    languages = [language.upper() for language in languages]
    languages = Languages.get_languages(languages)

    original_files = get_content(url)

    files = get_archives(original_files, languages)

    original_files = convert_to_original_files(original_files)

    xml = get_xml(files, languages)

    return response_content(original_files, files, xml)


if __name__ == '__main__':
    app.run()
