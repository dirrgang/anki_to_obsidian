from zipfile import ZipFile
import sqlite3
import markdownify

with ZipFile('decks.apkg', 'r') as zipObj:
    zipObj.extractall('tmp')

con = sqlite3.connect("tmp/collection.anki21")
cur = con.cursor()
cur.execute("SELECT tags, flds, sfld FROM notes")

h = markdownify.markdownify(cur.fetchone()[1])
print(h)