import binascii as ba
import os
from flask import Flask, make_response,render_template,request,session
import sqlite3 as sql
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad,unpad
app=Flask(__name__)
app.config.from_pyfile("config.py")
app.secret_key=os.urandom(16)
db=sql.connect(app.config.get("db_name","notes.sqlite"),check_same_thread=False)
cur=db.cursor()
db.execute("create table if not exists notes(valid varchar(32) primary key,validEnc varchar(32),note varchar)")
db.commit()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/open",methods=["POST"])
def openNote():
    encKey=request.form.get("key")
    encKey=(encKey*(16//len(encKey.encode('utf-8'))))if len(encKey)<16 else encKey
    encKey+=encKey[:16-len(encKey)]
    valid=request.form.get("valid")
    cur.execute("select * from notes where valid='{}'".format(valid))
    note=cur.fetchone()
    aes=AES.new(bytes(encKey.encode('utf-8')),AES.MODE_ECB)
    if note:
        validEnc=ba.unhexlify(note[1])
        validEncDec=unpad(aes.decrypt(validEnc,output=None),16).decode('utf-8')
        if valid==validEncDec:
            session["key"]=encKey
            session["valid"]=valid
            if note[2]=='':
                return ''
            return unpad(aes.decrypt(ba.unhexlify(note[2])),16).decode('utf-8')
        else:
            return "KeyPresent"
    else:
        session["key"]=encKey
        session["valid"]=valid
        validEnc=aes.encrypt(pad(bytes(valid.encode('utf-8')),16)).hex()
        db.execute("insert into notes values('{}','{}','')".format(valid,validEnc))
        db.commit()
        return "NoteCreated"

@app.route("/delete",methods=["DELETE"])
def deleteNote():
    valid=session["valid"]
    try:
        db.execute("delete from notes where valid='{}'".format(valid))
        db.commit()
        return "Success"
    except:
        return "Error"
    
@app.route("/update",methods=["POST"])
def updateNote():
    note=request.form.get("note","")
    valid=session["valid"]
    cur.execute("select * from notes where valid='{}'".format(valid))
    noteDb=cur.fetchone()
    encKey=session["key"]
    aes=AES.new(bytes(encKey.encode('utf-8')),AES.MODE_ECB)
    if note=='':
        return "Empty"
    encNote=aes.encrypt(pad(bytes(note.encode('utf-8')),16)).hex()
    if encNote==noteDb[2]:
        return "NoChange"
    db.execute("update notes set note='{}' where valid='{}'".format(encNote,valid))
    db.commit()
    return "Success"

if __name__=="__main__":
    app.run()