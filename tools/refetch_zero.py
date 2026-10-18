import sys, sqlite3
sys.path.insert(0,'/Users/stian/src/rettskriv')
from rettskriv.archaism import fetch, DB
conn=sqlite3.connect(DB)
for lang in ('nob','nno'):
    words=[w for (w,) in conn.execute("select word from freq where lang=? and old=0 and new=0",(lang,))]
    print(lang,len(words),flush=True)
    fetch(words, lang, refresh_zero=True)
print('done',flush=True)
