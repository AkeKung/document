from ast import parse
from flask import make_response,jsonify
from flask_jwt_extended import jwt_required,get_jwt
from flask_restful import Resource,reqparse
import mysql.connector,os

class LocModel:
    def __init__(self,historyId=None,documentId=None,userId=None,action=None,userAgent=None,dateUpdate=None):
        self.historyId  = historyId,
        self.documentId = documentId,
        self.userId     = userId,
        self.action     = action,
        self.userAgent  = userAgent,
        self.dateUpdate = dateUpdate

    def json(self):
        return {
            "historyId"     : self.historyId,
            "documentId"    : self.documentId,
            "userId"        : self.userId,
            "action"        : self.action,
            "userAgent"     : self.userAgent,
            "dateUpdate"    : self.dateUpdate
        }


    def save_to_db(self):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        sql="INSERT INTO history value (%s,%s,%s,%s,%s,%s)"
        val = (LocModel.current()+1,self.documentId,self.userId,self.action,self.userAgent,self.dateUpdate)
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()
        print('Save loc complete')

    @classmethod
    def current(cls):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        sql="SELECT max(id_history) FROM history"
        mycursor.execute(sql)
        result=mycursor.fetchone()
        mydb.close()
        return result[0]

    @classmethod
    def stats(cls,action):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        sql="SELECT * FROM history where action like '%{}%' ".format(action) 
        mycursor.execute(sql)
        result=mycursor.fetchall()
        mydb.close()
        list_attr=["historyId","documentId","userId","action","userAgent","dateUpdate"]
        result_json=[]
        if result:
            for i in result:
                loc=LocModel()
                for j in range(len(i)): 
                    setattr(loc,list_attr[j],i[j])
                result_json.append(loc.json())
        return result_json


    @classmethod
    def list_loc(cls,limit,offset):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        sql="SELECT * FROM history order by id_history DESC limit %s offset %s"
        mycursor.execute(sql, (limit,offset))
        result = mycursor.fetchall()
        mydb.close()
        list_attr=["historyId","documentId","userId","action","userAgent","dateUpdate"]
        result_json=[]
        if result:
            for i in result:
                loc=LocModel()
                for j in range(len(i)): 
                    setattr(loc,list_attr[j],i[j])
                result_json.append(loc.json())
        return result_json
class GetStats(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('action',
                        type=str,
                        location='args',
                        required=True,
                        help="This action cannot be blank.")
    @jwt_required()
    def get(self):
        params = GetStats.parser.parse_args()
        return make_response({
            'status':'success',
            'data':LocModel.stats(params['action'])
        },200)

class ViewLoc(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('limit',
                        type=int,
                        required=True,
                        location='args',
                        help="This limit cannot be blank.")
    parser.add_argument('offset',
                        type=int,
                        required=True,
                        location='args',
                        help="This offset cannot be blank.")
    @jwt_required()
    def get(self):
        params = ViewLoc.parser.parse_args()
        if params['limit'] < 0:
            return {
                'status':'failed',
                'message':'Invalid enter limit'
            },400 
        elif params['offset'] < 0:
            return {
                'status':'failed',
                'message':'Invalid enter offset'
            },400 
        return make_response({
            'status':'success',
            'data':LocModel.list_loc(params['limit'],params['offset']) 
        },200)
