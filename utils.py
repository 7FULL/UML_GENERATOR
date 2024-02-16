import base64
import json
import os
import re

import requests

from models.Archive import Archive
from models.OriginalFile import OriginalArchive

excluded_folders = ['node_modules', 'build', 'dist', 'coverage', 'lib', 'test', 'tests', 'demo',
                    'docs', 'doc', 'tmp', 'temp', 'vendor', 'assets', 'images', 'img', 'font', 'lock', 'log',
                    'gitignore', 'editorconfig', 'eslintrc', 'eslintignore', 'prettierrc', 'prettierignore', 'babelrc',
                    'babelignore', 'tsconfig', 'tsconfigignore', 'dockerignore', 'dockerfile', 'gitattributes',
                    'gitkeep', 'gitmodules', 'gitpod', 'gitpodignore', 'gitpod.yml', 'gitpod.dockerfile',
                    'gitpod.Dockerfile', 'gitpod.dockerignore', 'gitpod.dockerignore', '.idea', '.vscode', '.github',
                    '.gradle']

methods_regular_expressions = {
    'js': r'\b(?:async\s+)?function\s+(\w+)\s*\(.*\)\s*{',
    'java': r'\b(?:public|private|protected)\s+(?:static\s+)?\w+\s+(\w+)\s*\((.*?)\)',
    'py': r'\bdef\s+(\w+)\s*\(',
    'c': r'\b\w+\s+\w+\s*\(',
    'cpp': r'\b\w+\s+\w+::\w+\s*\(',
    'cs': r'\b\w+\s+\w+\s*\(',
    'rb': r'\bdef\s+(\w+)\s*\(',
    'go': r'\bfunc\s+(\w+)\s*\(',
    'swift': r'\bfunc\s+(\w+)\s*\(.*\)\s*->\s*\w+\s*{',
    'kt': r'\bfun\s+(\w+)\s*\(.*\)\s*{',
    'php': r'\b(?:public|private|protected)\s+function\s+(\w+)\s*\(',
    'html': r'<\s*(\w+)\s*[^>]*?>',
    'css': r'\.(\w+)\s*{',
    'scss': r'\.(\w+)\s*{',
    'less': r'\.(\w+)\s*{',
    'sql': r'CREATE\s+FUNCTION\s+(\w+)',
    'r': r'\bfunction\s*\((.*)\)',
    'sh': r'\bfunction\s+(\w+)\s*\(',
    'm': r'[-+]\s*\((\w+)\)',
    'pl': r'sub\s+(\w+)\s*\{',
    'rs': r'\bfn\s+(\w+)\s*\(',
    'dart': r'\b(?:void\s+)?(\w+)\s*\(',
    'coffee': r'\b(?:\w+\.)*(\w+)\s*=\s*\((.*)\)\s*[-=]>',
    'scala': r'\bdef\s+(\w+)\s*\(',
    'hs': r'\b(\w+)\s*::\s*.*\s*=>',
    'erl': r'\b(\w+)\s*\((.*)\)\s*->',
    'cr': r'\bdef\s+(\w+)\s*\(',
    'ex': r'\bdefp?\s+(\w+)\s*\(.*\)\s*do',
    'lisp': r'\b(def(?:un)?\s+(\w+))\s*\(',
    'lua': r'\bfunction\s+(\w+)\s*\(',
    'vim': r'function!\s*(\w+)',
    'nim': r'\bproc\s+(\w+)\s*\(.*\)\s*=$',
    'pas': r'\b(?:procedure|function)\s+(\w+)\s*;',
    'forth': r':\s+(\w+)\s*$',
    'ml': r'\blet\s+(\w+)\s*=\s*fun\s*',
    'fs': r'\b(?:let|member|static member)\s+(\w+)\s*=\s*fun\s*',
    'ts': r'\b(?:function|(?<!\.|\w)\w+\s*=\s*function|\w+\s*=\s*\((?:(?:\w+\s*,\s*)*\w*)?\)\s*=>)\s+([a-zA-Z_]\w*)\s*\(|(?<=class\s+[a-zA-Z_]\w*\s*{\s*)\b(?:\w+\s*=\s*)?(?:function|(?<!\.|\w)\w+\s*=\s*function|\w+\s*=\s*\((?:(?:\w+\s*,\s*)*\w*)?\)\s*=>)\s+([a-zA-Z_]\w*)\s*\(',
    'md': r'(?<=^|\n)\s*(#{1,6})\s+.*',
    'xml': r'<\s*(\w+)\s*[^>]*?>',
    'json': r'"(\w+)":\s*"?.*?"?',
    'yaml': r'(\w+):',
    'toml': r'(\w+)\s*=\s*.*',
    'haml': r'%(\w+)',
    'hbs': r'{{\s*(\w+)\s*}}',
    'jade': r'\b(\w+)\s*\(.*\)',
    'slim': r'\b(\w+)\s*\((?:.*\n*)*\s*\)',
    'ejs': r'<%\s*(\w+)\s*%>',
    'cshtml': r'@(?:model|.*).\s*(\w+)\s*\(.*\)\s*{',
}

attributes_regular_expressions = {
    'js': r'\w+\s*:\s*\b(?:const|let|var)\b',  # JavaScript
    'jsx': r'\w+\s*=\s*\{',  # JSX
    'java': r'\b\w+\b\s+\w+\s*;',  # Java
    'py': r'\b\w+\b\s*=',  # Python
    'c': r'\b\w+\b\s*=',  # C
    'cpp': r'\b\w+\b\s*=',  # C++
    'cs': r'\b\w+\b\s*=',  # C#
    'rb': r'\b\w+\b\s*=',  # Ruby
    'go': r'\b\w+\b\s*=',  # Go
    'swift': r'\b\w+\b\s*=',  # Swift
    'kt': r'\b\w+\b\s*=',  # Kotlin
    'kts': r'\b\w+\b\s*=',  # Kotlin Script
    'php': r'\b\w+\b\s*=',  # PHP
    'html': r'\b\w+\b\s*=',  # HTML
    'css': r'\b\w+\b\s*:',  # CSS
    'scss': r'\b\w+\b\s*:',  # SCSS
    'less': r'\b\w+\b\s*:',  # LESS
    'sql': r'\b\w+\b\s*=',  # SQL
    'r': r'\b\w+\b\s*<-',  # R
    'sh': r'\b\w+\b\s*=',  # Shell
    'm': r'\b\w+\b\s*=',  # Objective-C
    'pl': r'\b\w+\b\s*=',  # Perl
    'rs': r'\b\w+\b\s*=',  # Rust
    'dart': r'\b\w+\b\s*=',  # Dart
    'coffee': r'\b\w+\b\s*=',  # CoffeeScript
    'scala': r'\b\w+\b\s*=',  # Scala
    'hs': r'\b\w+\b\s*=',  # Haskell
    'erl': r'\b\w+\b\s*=',  # Erlang
    'cr': r'\b\w+\b\s*=',  # Crystal
    'ex': r'\b\w+\b\s*=',  # Elixir
    'lisp': r'\b\w+\b\s*=',  # Lisp
    'lua': r'\b\w+\b\s*=',  # Lua
    'vim': r'\b\w+\b\s*=',  # Vim
    'nim': r'\b\w+\b\s*=',  # Nim
    'pas': r'\b\w+\b\s*=',  # Pascal
    'forth': r'\b\w+\b\s*=',  # Forth
    'ml': r'\b\w+\b\s*=',  # OCaml
    'fs': r'\b\w+\b\s*=',  # F#
    'ts': r'\b\w+\b\s*:',  # TypeScript
    'md': r'\b\w+\b\s*:',  # Markdown
    'xml': r'\b\w+\b\s*=',  # XML
    'json': r'\b\w+\b\s*:',  # JSON
    'yaml': r'\b\w+\b\s*:',  # YAML
    'toml': r'\b\w+\b\s*=',  # TOML
    'haml': r'\b\w+\b\s*=',  # HAML
    'hbs': r'\b\w+\b\s*=',  # Handlebars
    'jade': r'\b\w+\b\s*=',  # Jade
    'slim': r'\b\w+\b\s*=',  # Slim
    'ejs': r'\b\w+\b\s*=',  # EJS
    'cshtml': r'\b\w+\b\s*='  # Razor
}


# Function to get the content of a repository
def get_content(url):
    token = os.getenv('GITHUB_TOKEN')

    # We replace the github.com with the api.github.com
    url = url.replace('github.com', 'api.github.com/repos')

    response = requests.get(url + '/contents',
                            headers={"Authorization": "Bearer "+token})

    return response.json()


def convert_to_original_files(archives):
    original_files = []
    for archive in archives:
        original_files.append(OriginalArchive(archive['name'], archive['html_url']))
    return original_files


def generate_class_cell(class_name, methods, attributes, initial_y, expected_height):
    # We calculate the maximum width of the class cell seeing wich method + parameters is the longest
    max_width = 0

    for method in methods:
        # Method is a tuple, the first element is the method name and the rest are the parameters
        method_name = method[0]
        parameters = method[1:]

        value_method = f'{method_name}(' + ', '.join(parameters) + ')'

        if len(value_method) > max_width:
            max_width = len(value_method)

    for parameter in attributes:
        if len(parameter) > max_width:
            max_width = len(parameter)

    # We check if the class name is longer than the methods and attributes
    if len(class_name) > max_width:
        max_width = len(class_name)

    max_width *= 7

    xml = f'''
            <mxCell id="{class_name}" value="{class_name}" style="swimlane;fontStyle=0;childLayout=stackLayout;horizontal=1;startSize=26;fillColor=none;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;" parent="1" vertex="1">
                <mxGeometry x="0" y="{initial_y}" width="{max_width}" height="{expected_height}" as="geometry">
                    <mxRectangle x="0" y="{initial_y}" width="{max_width-40}" height="30" as="alternateBounds" />
                </mxGeometry>
            </mxCell>'''

    y_offset = 30
    if len(methods) > 0:
        for method in methods:
            # Method is a tuple, the first element is the method name and the rest are the parameters
            method_name = method[0]
            parameters = method[1:]

            value_method = f'{method_name}(' + ', '.join(parameters) + ')'

            xml += f'''
                <mxCell id="{value_method + "_" + class_name}" value="{value_method}" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;" parent="{class_name}" vertex="1">
                    <mxGeometry x="0" y="{y_offset}" width="{max_width}" height="30" as="geometry" />
                </mxCell>'''
            y_offset += 30

    if len(attributes) > 0 and len(methods) == 0:
        separator_id = f'{class_name}_separador'

        # Separation line
        xml += f'''
                    <mxCell id="{separator_id}" value="" style="line;strokeColor=none;fillColor=#000000;strokeWidth=3;" parent="{class_name}" vertex="1">
                        <mxGeometry x="0" y="{y_offset}" width="{max_width}" height="1" as="geometry" />
                    </mxCell>'''

    if len(attributes) > 0:
        for parameter in attributes:
            xml += f'''
                <mxCell id="{parameter + "_" + class_name}" value="{parameter}" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;" parent="{class_name}" vertex="1">
                    <mxGeometry x="0" y="{y_offset}" width="{max_width}" height="30" as="geometry" />
                </mxCell>'''
            y_offset += 30

    return xml


def get_archives(response, languages):
    token = os.getenv('GITHUB_TOKEN')

    archives = []

    # We get the extensions of the languages
    extensions = []

    for language in languages:
        extensions += language

    for archive in response:
        try:
            if archive['type'] == 'file':
                # If the archive file has any of the extensions we are looking for, if the archive is not starting with a dot
                if any(archive['name'].endswith(extension) for extension in extensions) and not archive[
                    'name'].startswith('.'):
                    archives.append(Archive(archive, False))

            else:
                # We seach if its an excluded folder
                if archive['name'] not in excluded_folders:
                    archives += get_archives(requests.get(archive['url'], headers={
                        "Authorization": "Bearer "+token}).json(), extensions)
                else:
                    archives.append(Archive(archive, True))
        except TypeError as e:
            print(f'Error in {archive} archive. Error: {e}')
            pass

    return archives


def get_xml(archives, languages):
    token = os.getenv('GITHUB_TOKEN')

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <mxGraphModel dx="3312" dy="1989" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
            <root>
                <mxCell id="0" />
                <mxCell id="1" parent="0" />
        '''
    initial_y = 0

    for archive in archives:
        methods = []
        attributes = []

        if not archive.excluded:
            # We do a request to github to get the content of the file
            content = requests.get(archive.element['url'],
                                   headers={"Authorization": "Bearer "+token}).json()

            if content['encoding'] == 'base64':
                content = content['content']

                content = base64.b64decode(content).decode('utf-8')

                for language in languages:
                    methods += search_methods(content, language)
                    attributes += search_attributes(content, language)

                """
                print(f'Archive: {archive.element["name"]}')
                print(f'Methods: {methods}')
                print(f'Attributes: {attributes}')
                """

                expected_height = (len(methods) + len(attributes)) * 30

                # We add 30 extra pixels for the class name
                expected_height += 30

                xml += generate_class_cell(archive.element['name'], methods, attributes, initial_y, expected_height)

                initial_y += expected_height + 100
            else:
                print(f'Archive {archive.element["name"]} is not base64 encoded')

    xml += '''
            </root>
        </mxGraphModel>
    '''

    # We insert the xml in the archive ejemplo.xml
    with open('ejemplo.xml', 'w') as file:
        file.write(xml)

    return xml


def search_attributes(class_content, language):
    # We put every language in the array in lower case
    language = [lang.lower() for lang in language]

    attributes = []

    for lang in language:
        regular = attributes_regular_expressions.get(lang)
        if regular:
            attributes += re.findall(regular, class_content)

    # We remove the duplicates
    attributes = list(set(attributes))

    # If any of the attributes is a reserved word, we remove it
    reserved_words = ['abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 'const',
                      'continue', 'default', 'do', 'double', 'else', 'enum', 'extends', 'final', 'finally', 'float',
                      'for', 'if', 'implements', 'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new',
                      'package', 'private', 'protected', 'public', 'return', 'short', 'static', 'strictfp', 'super',
                      'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try', 'void', 'volatile',
                      'while', 'true', 'false', 'null']

    valid_attributes = [attribute for attribute in attributes if not any(reserved_word in attribute.split() for reserved_word in reserved_words)]

    return valid_attributes


def search_methods(class_content, language):
    # We put every language in the array in lower case
    language = [lang.lower() for lang in language]

    methods = []

    for lang in language:
        regular = methods_regular_expressions.get(lang)
        if regular:
            methods += re.findall(regular, class_content)

    return methods


def response_content(base_archives, archives, xml):
    data = {
        "base_archives": [archive.to_dict() for archive in base_archives],
        "archives": [archive.to_dict() for archive in archives],
        "xml": xml
    }

    return json.dumps(data)
