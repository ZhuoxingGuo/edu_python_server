# -*- coding: UTF-8 -*-
import sqlite3
from flask import Flask, jsonify, Response
from flask import request
import json
import os.path
import logging

g_path = 'classroom.db'
g_create_sql = "CREATE TABLE classroom(sdkappid INTEGER,classid TEXT,avroomid INTEGER,chatgroup INTEGER,wbchannel INTEGER)"

logging.basicConfig(filename="./logserver.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger('urbanGUI')

app = Flask(__name__)


@app.route('/edu_server/applyclassroomid', methods=['POST', 'GET'])
def hello():
    if request.method == 'POST':
        print request
        return "200"

    if request.method == 'GET':
        print request
        sdkappid = request.args.get("sdkappid")

        if sdkappid is None :
            res = {}
            res['status'] = -1
            res['info'] = "param is not corret"
            response = Response(json.dumps(res),
                                mimetype='application/json',
                                )
            return response
        else:
            res = {}
            res['data'] = get_classId(sdkappid)
            res['status'] =200
            res['info'] = "succ"
            response = Response(json.dumps(res),
                                mimetype='application/json',
                               )
            return response


@app.errorhandler(404)
def exception_handler(error):
    print error
    logger.error("exception_handler %s", error)

    error_info = {}
    error_info['status'] = 404
    error_info['info'] = "not found"

    response = Response(json.dumps(error_info),
                        mimetype='application/json',
                        status=error.code)
    return response


def initDb():
    global g_path
    if not os.path.exists(g_path):
        logger.info("create a database")
        print "create database..."
        conn = sqlite3.connect(g_path)
        cur = conn.cursor()
        cur.execute(g_create_sql)
        conn.commit()
        conn.close()
    else:
        logger.info("already has database")


def get_classId(sdkappid):
    print "get RoomClassId from ->", sdkappid
    sql = "SELECT * FROM classroom WHERE sdkappid=" + str(sdkappid) + "    "
    conn = sqlite3.connect(g_path)
    cur = conn.cursor()
    results = cur.execute(sql).fetchall()
    response= {}
    if 0 == len(results):
        print "插入一个新的sdkappid"
        avroomid = 1001
        chatgroup = avroomid
        wbchannel = 1002
        classid = str(avroomid)+"||"+str(chatgroup)+"||"+str(wbchannel)
        conn.execute("INSERT INTO classroom (sdkappid, classid, avroomid, chatgroup,wbchannel) VALUES (?, ?, ?, ?, ?)",
                     (sdkappid, classid, avroomid, chatgroup, wbchannel))
        conn.commit()
        response['classid'] = classid
        response['avroomid'] = avroomid
        response['chatgroup'] = chatgroup
        response['wbchannel'] = wbchannel
        return response
    else:
        for row in results:
            sdkappid = row[0]
            avroomid = row[2]+2
            chatgroup = row[3]+2
            wbchannel = row[4]+2
            classid = str(avroomid)+"||"+str(chatgroup)+"||"+str(wbchannel)

            # 更新数据库
            conn = sqlite3.connect(g_path)
            conn.execute(''' UPDATE classroom
              SET classid = ?,
                  avroomid = ?,
                  chatgroup = ?,
                  wbchannel = ?
              WHERE sdkappid = ?''', (classid, avroomid, chatgroup, wbchannel,sdkappid))
            conn.commit()

            response['classid'] = classid
            response['avroomid'] = avroomid
            response['chatgroup'] = chatgroup
            response['wbchannel'] = wbchannel
        return response


if __name__ == "__main__":
    initDb()
    print "logserver listen 5000"
    app.debug = True
    app.run()
