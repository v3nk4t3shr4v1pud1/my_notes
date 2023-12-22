from flask import Flask,render_template,request
import pymongo as pmdb
app=Flask(__name__)
app.config.from_pyfile("config.py")
client=pmdb.MongoClient(app.config.get("db_url","localhost"),app.config.get("db_port",27017))
db=client.get_database(app.config.get("db_name","notes"))
colls=db.get_collection(app.config.get("db_coll_name","notes"))

@app.route("/")
def home():
    return render_template("index.html")

if __name__=="__main__":
    app.run()