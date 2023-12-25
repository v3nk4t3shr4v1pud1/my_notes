import binascii as ba
import os
from flask import Flask, make_response,render_template,request,session
import sqlite3 as sql
import pymongo as pmdb
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad,unpad
app=Flask(__name__)
app.config.from_pyfile("config.py")
app.secret_key=os.urandom(16)
client=pmdb.MongoClient(app.config.get("db_client","localhost"),app.config.get("db_port",27017))
db=client.get_database(app.config.get("db_name","notes"))
coll=db.get_collection(app.config.get("coll_name","notes"))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/open",methods=["POST"])
def openNote():
    encKey=request.form.get("key")
    encKey=(encKey*(16//len(encKey.encode('utf-8'))))if len(encKey)<16 else encKey
    encKey+=encKey[:16-len(encKey)]
    valid=request.form.get("valid")
    note=coll.find_one({"valid":valid})
    aes=AES.new(bytes(encKey.encode('utf-8')),AES.MODE_ECB)
    if note:
        validEnc=ba.unhexlify(note["validEnc"])
        validEncDec=unpad(aes.decrypt(validEnc,output=None),16).decode('utf-8')
        if valid==validEncDec:
            session["key"]=encKey
            session["valid"]=valid
            if note["note"]=='':
                return ''
            return unpad(aes.decrypt(ba.unhexlify(note["note"])),16).decode('utf-8')
        else:
            return "KeyPresent"
    else:
        session["key"]=encKey
        session["valid"]=valid
        validEnc=aes.encrypt(pad(bytes(valid.encode('utf-8')),16)).hex()
        coll.insert_one({"valid":valid,"validEnc":validEnc,"note":""})
        return "NoteCreated"

@app.route("/delete",methods=["DELETE"])
def deleteNote():
    valid=session["valid"]
    try:
        coll.delete_one({"valid":valid})
        return "Success"
    except:
        return "Error"
    
@app.route("/update",methods=["POST"])
def updateNote():
    note=request.form.get("note","")
    valid=session["valid"]
    noteDb=coll.find_one({"valid":valid})
    encKey=session["key"]
    aes=AES.new(bytes(encKey.encode('utf-8')),AES.MODE_ECB)
    if note=='' and noteDb["note"]=='':
        return "Empty"
    encNote=aes.encrypt(pad(bytes(note.encode('utf-8')),16)).hex()
    if encNote==noteDb["note"]:
        return "NoChange"
    coll.update_one({"valid":valid},{"$set":{"note":encNote}})
    return "Success"

if __name__=="__main__":
    app.run()