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
import os
import markdownify as md

from pathvalidate._filename import sanitize_filename


def open_apkg(file: str):

    with ZipFile(file, 'r') as zip_obj:
        zip_obj.extractall('tmp')

    con = sqlite3.connect("tmp/collection.anki21")
    cur = con.cursor()
    cur.execute("SELECT tags, flds, sfld FROM notes")
    return cur


def remove_cloze(text: str):
    cloze_regex = re.compile(r'({{c\d+::.*?}})')
    text_list = re.split(cloze_regex, text)

    result = ""
    for item in text_list:
        if item[0:3] == r'{{c':
            result += re.sub(r'{{c\d+::', '', item)[:-2]
        else:
            result += item
    return result


def modify_mathjax(text: str):

    mjregex = re.compile(r'(\\\(.*?\\\))')
    text_list = re.split(mjregex, text)

    result = ""
    for item in text_list:
        if item[0:2] == r'\(':
            result += '$'+item[2:-2].strip()+'$'
        else:
            result += item

    return result


def sanitize_html(text: str):

    result = re.sub(r'.+?\x1f', '', text, 1)
    result = re.sub(r'\x1f', '', result)
    result = re.sub(r'<br></b>', r'</b><br>', result)
    result = re.sub(r'<b><br>', r'<br><b>', result)
    result = re.sub(r'&nbsp;', ' ', result)
    result = re.sub(r'<div>', r'<br><div>', result)
    result = re.sub(r'</div>', r'</div><br>', result)
    result = re.sub(r'</dd></dl>', r'</dd></dl><br>', result)
    result = re.sub(r'', '\n', result)

    return result


def transform_format(text: str):
    result = sanitize_html(text)
    result = md.markdownify(result, heading_style="ATX", strip=['a'])
    result = re.sub(r'\\_', r'_', result)
    result = remove_cloze(result)
    result = modify_mathjax(result)

    return result


def save_file(title: str, content: str, tags: list[str]):

    dirname = os.path.dirname(__file__)+'/export'
    filename = sanitize_filename(title.strip()+'.md')
    filename = os.path.join(
        dirname, filename)

    file = open(filename, mode="w", encoding='utf-8')

    file.write(content)
    file.write('\n')

    for tag in tags:
        file.write('#'+tag.strip()+' ')


if __name__ == "__main__":
    cur = open_apkg('decks.apkg')

    records = cur.fetchall()

    for row in records:
        title = row[2]
        body = row[1]
        tags = row[0].split()

        body = transform_format(body)

        save_file(title, body, tags)
