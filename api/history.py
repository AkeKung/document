from ast import parse
from datetime import datetime
import re
from flask import make_response,jsonify
from flask_jwt_extended import jwt_required,get_jwt
from flask_restful import Resource,reqparse
import mysql.connector,os

class LocModel:
    def __init__(self,historyId=None,documentId=None,userId=None,action=None,userAgent=None,dateUpdate=None,username=None):
        self.historyId  = historyId,
        self.documentId = documentId,
        self.userId     = userId,
        self.action     = action,
        self.userAgent  = userAgent,
        self.dateUpdate = dateUpdate,
        self.username = username

    def json(self):
        return {
            "historyId"     : self.historyId,
            "documentId"    : self.documentId,
            "username"      : self.username,
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
    def stats(cls,action,month):
        cond =" and YEARWEEK(date_update,1)  =YEARWEEK(NOW())"
        if month:
            cond = "and Month(date_update) = {}".format(month) 
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        sql="SELECT DATE(date_update) ,count(*) FROM history where action like '%{}%' {} group by DATE(date_update)".format(action,cond)
        mycursor.execute(sql)
        result=mycursor.fetchall()
        mydb.close()
        result_json=[]
        print(result)
        if result:
            for i in result:
                result_json.append({"date_update":i[0],"value":i[1]})
        return {"stats": result_json}

    @classmethod
    def MostRangeViewDoc(cls):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        sql="SELECT doc_id ,count(*) FROM history where action like '%view%' group by doc_id order by count(*) DESC limit 10"
        mycursor.execute(sql)
        result=mycursor.fetchall()
        mydb.close()
        result_json=[]
        print(result)
        if result:
            for i in result:
                result_json.append({"documentId":i[0],"value":i[1]})
        return {"stats": result_json}



    @classmethod
    def list_loc(cls,limit,offset):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        sql="SELECT  id_history,username,doc_id,action,user_agent,date_update,u_id FROM history left join user on user_id=u_id group by id_history DESC having id_history limit %s offset %s"
        mycursor.execute(sql, (limit,offset))
        result = mycursor.fetchall()
        mydb.close()
        list_attr=["historyId","username","documentId","action","userAgent","dateUpdate","userId"] 
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
    parser.add_argument('type',
                        type=int,
                        required=True,
                        location='args',
                        help="This action cannot be blank.")    
    parser.add_argument('opt',
                        type=str,
                        required=True,
                        location='args',
                        help="This action cannot be blank.")     
    Monthparser = reqparse.RequestParser()
    Monthparser.add_argument('month',
                        type=int,
                        required=True,
                        location='args',
                        help="This action cannot be blank." 
                        )
    @jwt_required()
    def get(self):
        params = GetStats.parser.parse_args()
        if params['type'] ==0 :
            if params['opt'] == "w":
                return make_response({
                    "status" : "success",
                    "data": LocModel.stats("insert",None)
                },200)
            else :
                mparams = GetStats.Monthparser.parse_args()
                if mparams['month']>12 or mparams['month'] <1:
                        return {{
                            "status": "failed",
                            "message": "Not Invalid month"},400}
                else:
                    month = mparams['month']
                month = datetime.today().month
            return make_response({
                'status':'success',
                'data':LocModel.stats("insert",month)
                },200)
        elif params['type'] ==1 :
            return {
                    'status':'success',
                    'data': LocModel.MostRangeViewDoc()
                },200
        

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
