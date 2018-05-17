# -*- coding: UTF-8 -*-
import sqlite3
import random

from flask import Flask, jsonify, Response
from flask import request
import requests
import json
import os.path
import logging

g_path = 'classroom.db'
g_create_sql = "CREATE TABLE classroom(sdkappid INTEGER,classid TEXT,avroomid INTEGER,chatgroup INTEGER,wbchannel INTEGER)"

logging.basicConfig(filename="./eduserver.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger('urbanGUI')

app = Flask(__name__)


@app.route('/ticsdk_server', methods=['POST', 'GET'])
def handle_request():
    logger.info("request %s", request)
    print request

    data = request.get_data()
    jsondata = json.loads(data)

    if jsondata['cmd'] == "apply_classroom_id":  ###申请房间请求
        sdkappid = request.args.get("sdkappid")
        if sdkappid is None:  ###sdkappid 为空
            res = {}
            res['error_code'] = -12003
            res['error_msg'] = "sdkappid is None"
            response = Response(json.dumps(res),
                                mimetype='application/json',
                                )
            return response
        else:  ###正常请求
            res = {}
            res['data'] = get_classId(sdkappid)  ###为这个sdkappid分配ID
            res['error_code'] = 0
            res['error_msg'] = ""
            response = Response(json.dumps(res),
                                mimetype='application/json',
                                )
            return response
    elif jsondata['cmd'] == "create_classroom":  ###业务server请求创建房间
        logger.info(" 0  create_classroom request  %s   ", request)
        print " 0  create_classroom request    ", request
        res = {}
        sdkappid = request.args.get("sdkappid")
        identifier = request.args.get("identifier")
        usersig = request.args.get("usersig")

        ##必须具备TPYE Name  sdkAPPID 如果任意有一个为空 直接退出
        # if jsondata['Type'] == None | jsondata['Name'] == None | jsondata['sdkappid'] == None:
        if sdkappid == None:
            res['error_code'] = -1
            res['error_msg'] = "param is not correct! "
            res['classid'] = ''
            res['chatgroup_info'] = ''
            res['wbchannel_info'] = ''
            response = Response(json.dumps(res),
                                mimetype='application/json',
                                )
            return response

        ##先获取房间ID
        result = get_classId(sdkappid)
        wbchannel_id = str(result['wbchannel'])
        chatgroup_id = str(result['chatgroup'])

        logger.info(" 1 create_classroom request  %s   param %s  classid  %s ", request, jsondata, result)
        print " 1 create_classroom request   ", request
        print " 1 create_classroom param  ", jsondata
        print " 1 create_classroom classid  ", result

        # 创建聊天群组
        ran = random.randint(0, 99999999)
        create_chatgroup_restapi = 'https://console.tim.qq.com/v4/group_open_http_svc/create_group?usersig=' + usersig + '&identifier=' + str(
            identifier) + "&sdkappid=" + str(sdkappid) + '&random=' + str(ran) + '&contenttype=json'
        logger.info("create_room_restapi  %s    ", create_chatgroup_restapi)
        chatgroup = requests.post(create_chatgroup_restapi,
                                  data={'Type': 'ChatRoom',
                                        'Name': 'chatgroup', 'GroupId': chatgroup_id})
        logger.info(" 2 chatgroup  %s    ", chatgroup)
        print " 2 chatgroup  %s    ", chatgroup

        # 创建白板通道
        ran2 = random.randint(0, 99999999)
        create_wbchannel_restapi = 'https://console.tim.qq.com/v4/group_open_http_svc/create_group?usersig=' + usersig + '&identifier=' + str(
            identifier) + "&sdkappid=" + str(sdkappid) + '&random=' + str(ran2) + '&contenttype=json'
        logger.info("create_room_restapi  %s    ", create_wbchannel_restapi)
        wbchannel = requests.post(create_wbchannel_restapi,
                                  data={'Type': 'ChatRoom',
                                        'Name': 'wbchannel', 'GroupId': wbchannel_id})
        logger.info(" 3 wbchannel  %s    ", wbchannel)
        print" 3 wbchannel  %s    ", wbchannel
        # 返回值
        if chatgroup['ErrorCode'] == 0 & wbchannel['ErrorCode'] == 0:
            res['error_code'] = 0
            res['error_msg'] = ""
            res['classid'] = result['classid']
            res['chatgroup_info'] = ''
            res['wbchannel_info'] = ''
        else:
            res['error_code'] = -1
            res['error_msg'] = ""
            res['classid'] = ''
            res['chatgroup_info'] = chatgroup
            res['wbchannel_info'] = wbchannel

        response = Response(json.dumps(res),
                            mimetype='application/json',
                            )
        return response

    elif jsondata['cmd'] == "destroy_classroom":  ###业务server请求创建房间
        pass

    else:  ###cmd 不能识别
        res = {}
        res['error_code'] = -12003
        res['error_msg'] = "cmd is wrong!! "
        response = Response(json.dumps(res),
                            mimetype='application/json',
                            )
        return response

        # if request.method == 'GET':
        #     print request
        #     res = {}
        #     res['error_code'] = -1
        #     res['error_msg'] = "this is get request"
        #     response = Response(json.dumps(res),
        #                         mimetype='application/json',
        #                         )
        #     return response


@app.errorhandler(404)
def exception_handler(error):
    print error
    logger.error("exception_handler %s", error)

    error_info = {}
    error_info['error_code'] = 404
    error_info['error_msg'] = "not found"

    response = Response(json.dumps(error_info),
                        mimetype='application/json',
                        status=error.code)
    return response


@app.errorhandler(400)
def exception_handler(error):
    print error
    logger.error("exception_handler 400 %s", error)

    error_info = {}
    error_info['error_code'] = 400
    error_info['error_msg'] = "400 Bad Request"

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
    response = {}
    if 0 == len(results):
        print "插入一个新的sdkappid"
        avroomid = 1001
        chatgroup = avroomid
        wbchannel = 1002
        classid = str(avroomid) + "##" + str(chatgroup) + "##" + str(wbchannel)
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
            avroomid = row[2] + 2
            chatgroup = row[3] + 2
            wbchannel = row[4] + 2
            classid = str(avroomid) + "##" + str(chatgroup) + "##" + str(wbchannel)

            # 更新数据库
            conn = sqlite3.connect(g_path)
            conn.execute(''' UPDATE classroom
              SET classid = ?,
                  avroomid = ?,
                  chatgroup = ?,
                  wbchannel = ?
              WHERE sdkappid = ?''', (classid, avroomid, chatgroup, wbchannel, sdkappid))
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
