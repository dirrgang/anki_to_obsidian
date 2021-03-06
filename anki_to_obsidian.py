#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Dennis Irrgang"
__version__ = "0.1.0"
__license__ = "AGPL-3.0"

from sqlite3.dbapi2 import Cursor
from zipfile import ZipFile
import sqlite3
import re
import os
import shutil
import sys
import argparse
import markdownify as md

from pathvalidate._filename import sanitize_filename


def open_apkg(file: str) -> Cursor:
    """Opens .apkg file for exporting Anki notes from the sqlite databse inside

    Parameters:
    file (str): File path of .apkg file.

    Returns:
    cur:SQlite cursor set on first row of note files.

   """

    with ZipFile(file, 'r') as zip_obj:
        zip_obj.extractall('tmp')

    con = sqlite3.connect("tmp/collection.anki21")
    cur = con.cursor()
    cur.execute("SELECT tags, flds, sfld FROM notes")
    return cur


def remove_cloze(text: str) -> str:
    """Removes Anki's Cloze indicators ({{}})

    Parameters:
    text (str): String with the to-be-removed Cloze indicators.

    Returns:
    text:Cloze-free string.

   """
    cloze_regex = re.compile(r'({{c\d+::.*?}})')
    text_list = re.split(cloze_regex, text)

    result = ""
    for item in text_list:
        if item[0:3] == r'{{c':
            result += re.sub(r'{{c\d+::', '', item)[:-2]
        else:
            result += item
    return result


def convert_mathjax(text: str) -> str:
    """Converts the Mathjax tokens from Anki to Markdown appropriate $"""

    # We need to split the text into mathjax groups and non-mathjax groups
    mjregex = re.compile(r'(\\\(.*?\\\))')
    text_list = re.split(mjregex, text)

    result = ""

    # Since we know that the Mathjax tokens are of fixed length, we can simply
    # truncate the groups on both sides by the length of the Mathjax tokens.
    for item in text_list:
        if item[0:2] == r'\(':
            result += '$'+item[2:-2].strip()+'$'
        else:
            result += item

    return result


def sanitize_html(text: str) -> str:
    '''Sanitizes incoming HTML to avoid certain characters that break markdown
    or otherwise do not work with it.'''

    # Removes duplicate title in the beginning of every file.
    result = re.sub(r'.+?\x1f', '', text, 1)

    # Removes unnecessary or "broken" HTML codes
    result = re.sub(r'\x1f', '', result)
    result = re.sub(r'&nbsp;', ' ', result)
    result = re.sub(r'', '\n', result)

    # Anki sometimes mixes the order of HTML tokens which can break during the
    # markdown conversion stage
    result = re.sub(r'<br></b>', r'</b><br>', result)
    result = re.sub(r'<b><br>', r'<br><b>', result)

    # CSS formatting normally ensures adequate spacing between <div> and
    # previous content, this is not the case in Markdown format, hence we need
    # to add some linebreaks on our own
    result = re.sub(r'<div>', r'<br><div>', result)
    result = re.sub(r'</div>', r'</div><br>', result)
    result = re.sub(r'</dd></dl>', r'</dd></dl><br>', result)

    return result


def transform_format(text: str) -> str:
    '''Formats Anki HTML Code into Markdown'''

    result = sanitize_html(text)
    result = md.markdownify(result, heading_style="ATX", strip=['a'])
    # Escaping artifact that breaks Mathjax
    result = re.sub(r'\\_', r'_', result)
    result = remove_cloze(result)
    result = convert_mathjax(result)

    return result


def save_file(name: str, content: str, tags: str) -> None:
    """Stores the file in the ./export/ directory

    Parameters:
    name (str): Name of the file
    content (str): Content to be written into the file body.
    tags (str): Tags to be added in the #tag format at the end of the content.

    Returns:
    None

   """
    dirname = os.path.dirname(__file__)+'/export'
    filename = sanitize_filename(re.sub(r':', r' -', name).strip()+'.md')
    filename = os.path.join(
        dirname, filename)

    file = open(filename, mode="w", encoding='utf-8')

    file.write(content)
    file.write('\n')

    for tag in tags.split():
        file.write('#'+tag.strip()+' ')


def cleanup() -> None:
    '''Removes temporary files and tmp directory.'''
    dir_path = './tmp/'

    try:
        shutil.rmtree(dir_path)
    except OSError as exception:
        print(f"Error: {dir_path} : {exception.strerror}")


def init_argparse() -> argparse.ArgumentParser:
    '''Initialises argparser for CLI use.'''
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [FILE]...",

        description="Convert Anki cards from an .apkg deck into Obsidian compatible markdown files."
    )

    parser.add_argument(
        "-v", "--version", action="version",
        version=f"{parser.prog} {__version__}"
    )

    parser.add_argument('files', nargs='*')

    return parser


def convert(file) -> None:
    '''Converts apkg file and exports the .md files into ./export'''
    cur = open_apkg(file)

    records = cur.fetchall()

    for row in records:
        title = row[2]
        body = row[1]
        tags = row[0]

        body = transform_format(body)

        save_file(title, body, tags)

    cleanup()


def main() -> None:
    """Converts Anki cards from .apkg files to Obsidian.md compatible markdown files

    Parameters:
    None (passed through CLI, see argparse/help)

    Returns:
    None

   """

    parser = init_argparse()

    args = parser.parse_args()

    for file in args.files:

        if file == "-":

            continue

        try:

            convert(file)

        except (FileNotFoundError, IsADirectoryError) as err:

            print(f"{sys.argv[0]}: {file}: {err.strerror}", file=sys.stderr)


if __name__ == "__main__":
    main()
