#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Dennis Irrgang"
__version__ = "0.1.0"
__license__ = "AGPL-3.0"

from zipfile import ZipFile
import sqlite3
import re
import markdownify as md
import os
from pathvalidate import sanitize_filename


def open_apkg(file):

    with ZipFile(file, 'r') as zip_obj:
        zip_obj.extractall('tmp')

    con = sqlite3.connect("tmp/collection.anki21")
    cur = con.cursor()
    cur.execute("SELECT tags, flds, sfld FROM notes")
    return cur


def remove_cloze(text):
    cloze_regex = re.compile(r'({{c\d+::.*?}})')
    text_list = re.split(cloze_regex, text)

    result = ""
    for item in text_list:
        if item[0:3] == r'{{c':
            result += re.sub(r'{{c\d+::', '', item)[:-2]
        else:
            result += item
    return result


def modify_mathjax(text):

    mjregex = re.compile(r'(\\\(.*?\\\))')
    text_list = re.split(mjregex, text)

    result = ""
    for item in text_list:
        if item[0:2] == r'\(':
            result += '$'+item[2:-2].strip()+'$'
        else:
            result += item

    return result


if __name__ == "__main__":
    cur = open_apkg('decks.apkg')

    records = cur.fetchall()

    for row in records:

        dirname = os.path.dirname(__file__)
        filename = os.path.join(
            dirname, 'export/'+sanitize_filename(row[2]).strip()+'.txt')

        f = open(filename, mode="w")

        body = remove_cloze(row[1])
        body = modify_mathjax(body)

        body = md.markdownify(body, heading_style="ATX")

        body = re.sub(r'', '\n', body)
        f.write(body)
        f.write('\n')

        tags = row[0].split()

        for tag in tags:
            f.write('#'+tag+' ')
