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


def open_apkg():

    with ZipFile('decks.apkg', 'r') as zip_obj:
        zip_obj.extractall('tmp')

    con = sqlite3.connect("tmp/collection.anki21")
    cur = con.cursor()
    cur.execute("SELECT tags, flds, sfld FROM notes")

    mjregex_open = re.compile(re.escape('\('))
    mjregex_close = re.compile(re.escape('\)'))
    html_body = re.sub(mjregex_open, '$', re.sub(
        mjregex_close, '$', cur.fetchone()[1]))

    markdown_body = md.markdownify(html_body, heading_style="ATX")
    print(markdown_body)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    open_apkg()
