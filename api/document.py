from flask import make_response,request
from flask_restful import Resource,reqparse
from flask_jwt_extended import jwt_required,get_jwt

import mysql.connector,os
#from db import mydb

from person import PersonModel
from history import LocModel

from datetime import datetime
mydb= mysql.connector.connect(host="localhost",user="root",passwd="",database="doc")

class DocumentModel:
    def __init__(self,documentId=None,title=None,sendAddress=None,receiver=None,dateWrite=None,signature=None,dateUpdate=None):
        self.documentId     = documentId,
        self.title          = title,
        self.sendAddress    = sendAddress,
        self.receiver       = receiver,
        self.dateWrite      = dateWrite,
        self.signature       = signature,
        self.dateUpdate     = dateUpdate

    def json(self,detail=None):
        result= {
            "documentId"   : self.documentId,
            "title"         : self.title,
            "sendAddress"   : self.sendAddress ,
            "receiver"      : self.receiver,
            "dateWrite"     : self.dateWrite,
            "dateUpdate"    : self.dateUpdate
        }
        if detail:
            self.signature = detail
            result['signature']=self.signature
        return result
    
    @classmethod
    def current_doc(cls):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        mycursor.execute("SELECT Max(documentId) FROM document")
        result = mycursor.fetchone()
        mydb.close()
        #print("result: ",result)
        if None not in result: 
            return result[0]
        else: 
            return 0
    
    def save_to_db(self):
        if(self.signature):
            for i in self.signature:
                check=PersonModel.tokenization_name(i['personName'])
                if(len(check)<3):return False
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query = "Update document set title = %s, sendAddress = %s, receiver =%s,dateWrite = %s where documentId = %s"
        mycursor.execute(query,(self.title, self.sendAddress,self.receiver,self.dateWrite,self.documentId))
        mydb.commit()
        mydb.close()
        for i in self.signature:
            self.save_signature(i)
        return True

    @classmethod
    def current_signature(cls):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        mycursor.execute("SELECT Max(id_signature) FROM signature")
        result = mycursor.fetchone()
        mydb.close()
        #print("result: ",result)
        if None not in result: 
            return result[0]
        else: 
            return 0

    def save_signature(self,signature):
        person=PersonModel()
        id_person=person.save_person(signature['personName'])
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        sql = "INSERT INTO signature (id_signature,doc_id,person_id,signature_role,signature_img) VALUES (%s,%s,%s,%s,%s)"
        val = (self.current_signature()+1,self.documentId,id_person,signature['personRole'],signature['signatureImg'])
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()
    
    def update_db(self):
        print(self.title,self.sendAddress,self.receiver,self.dateWrite,self.documentId) 
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor(buffered=True)
        query = "UPDATE document SET title = %s, sendAddress = %s, receiver = %s, dateWrite = %s where documentId = %s"
        mycursor.execute(query,(self.title,self.sendAddress,self.receiver,self.dateWrite,self.documentId))
        mydb.commit()
        for i in self.signature:
            self.update_signature(i)
        mydb.close()

    def update_signature(self,signature):
        #print('signature',signature)
        PersonModel.update_person(signature['personId'],signature['personName'])
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        sql = "Update signature set signature_role = %s,signature_img = %s where person_id = %s"
        val = (signature['personRole'],signature['signatureImg'],signature['personId'])
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()

    @classmethod
    def find_doc_by_id(cls,documentId):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query = f"SELECT documentId,title,sendAddress,receiver,dateWrite,Max(date_update) FROM document join history on history.doc_id = document.documentId WHERE documentId= {documentId} "
        #print('query: ',query)
        mycursor.execute(query)
        result = mycursor.fetchone()
        mydb.close()
        if None != result[0]:
            doc=DocumentModel()
            dict_doc=['documentId','title','sendAddress','receiver','dateWrite','dateUpdate']
            for j in range(len(dict_doc)):
                value=result[j]
                if value:
                    setattr(doc,dict_doc[j],value)
                else :setattr(doc,dict_doc[j],'')
        else:
            doc=None
        mydb.close()
        return doc

    @classmethod
    def find_signature_in_doc(cls,doc_id):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query = "SELECT person_id,person_tname,person_fname,person_lname,signature_role,signature_img FROM signature join persons on signature.person_id = persons.id_person WHERE doc_id= (%s)"
        mycursor.execute(query, (doc_id,))
        result = mycursor.fetchall()
        mydb.close()
        signature=[]
        for i in result:
            signature.append({'personId': i[0],'personName':f"{i[1]} {i[2]} {i[3]}",'personRole':i[4],'signatureImg':i[5]})
        return signature

    @classmethod
    def list_doc(cls,limit,offset,cond):
        text=''
        if cond:
            if len(cond) ==1:
                text+=f'where dateWrite {cond[0]}'
            elif len(cond)==2:
                text+=f'where dateWrite {cond[0]} and dateWrite {cond[1]}'
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query="SELECT documentId,title,sendAddress,receiver,dateWrite,Max(date_update) FROM document join history on document.documentId = history.doc_id {2} group by documentId ORDER BY documentId DESC limit {0} offset {1}".format(limit,offset,text)
        print(query)
        mycursor.execute(query)
        result = mycursor.fetchall()
        mydb.close()
        list=[]
        dict_doc=['documentId','title','sendAddress','receiver','dateWrite','dateUpdate']
        for i in result:
            for j in range(len(i)):
                setattr (cls,dict_doc[j],i[j])
            list.append(cls.json(cls))
        return list

    @classmethod
    def delete_doc(cls,id):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query = f"delete from document where documentId = {id}"
        #print(query)
        mycursor.execute(query)#,multi=True)
        mydb.commit()
        mydb.close()

    @classmethod
    def search_doc_by_key(cls,keyword,limit,offset,cond):
        text=''
        if cond:
            if len(cond) ==1:
                text+=f'Having dateWrite {cond[0]}'
            elif len(cond)==2:
                text+=f'Having dateWrite {cond[0]} and dateWrite {cond[1]}'
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        query="""
            SELECT documentId,title,sendAddress,receiver,dateWrite,date_update From document join history on  documentId = doc_id
            where documentId in ( 
            SELECT DISTINCT documentId 
            from document left join signature on document.documentId = signature.doc_id 
                          left join persons on persons.id_person = signature.person_id 
            where documentId like '%{0}%' or title like '%{0}%' or sendAddress like '%{0}%'
                  or receiver like '%{0}%' or DATE_FORMAT(dateWrite,'%Y-%m-%d') like '%{0}%'
                  or signature_role like '%{0}%' or person_tname like '%{0}%' or person_fname like '%{0}%' or person_lname like '%{0}%')
            group by documentId {3} ORDER BY documentId DESC limit {1} offset {2};
        """.format(keyword,limit,offset,text)
        print(query)
        mycursor.execute(query)
        result = mycursor.fetchall()
        mydb.close()
        list=[]
        dict_doc=['documentId','title','sendAddress','receiver','dateWrite','dateUpdate']
        for i in result:
            for j in range(len(dict_doc)):
                setattr(cls,dict_doc[j],i[j])
            list.append(cls.json(cls))
        return list

    @classmethod
    def save_page(cls,documentID,pageNum,url):
        num = DocumentModel.current_page()
        if(not num):
            num = 0
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        query=f"INSERT INTO pages values ({num+1},{documentID},{pageNum},'{url}')"
        mycursor.execute(query)
        mydb.commit()
        mydb.close()

    @classmethod
    def current_page(cls):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        query=f"SELECT Max(id_pages) from pages"
        mycursor.execute(query)
        result = mycursor.fetchone()
        mydb.close()
        return result[0]

    @classmethod
    def get_pages(cls,documentID):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor=mydb.cursor()
        query=f"SELECT num_page,url_page from pages where doc_id = {documentID}"
        mycursor.execute(query)
        result = mycursor.fetchall()
        mydb.close()
        list=[]
        if result:
            for i in result:
                dict_page={}
                dict_page[i[0]]=i[1]
                list.append(dict_page)
            return list
        else:return 0

class ViewPages(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('documentId',
                        type=int,
                        required=True,
                        help="This limit cannot be blank.",
                        location='args')

    @jwt_required()
    def get(self):
        params = ViewPages.parser.parse_args()
        pages=DocumentModel.get_pages(params['documentId'])
        if pages:
            return {
                'status':'success',
                'data': pages
            }
        else:
            return {
                'status':'failed',
                'message': "documentId don't store data"
            }
        

class ViewDocuments(Resource):

    Getparser = reqparse.RequestParser()
    Getparser.add_argument('limit',
                            type=int,
                            required=True,
                            help="This limit cannot be blank.",
                            location='args')
    Getparser.add_argument('offset',
                            type=int,
                            required=True,
                            help="This field cannot be blank.",
                            location='args'
                            )
    Getparser.add_argument('word',
                        type=str,
                        location='args'
                        )
    Getparser.add_argument('startDate',
                        type=str,
                        location='args',
                        )
    Getparser.add_argument('endDate',
                        type=str,
                        location='args'
                        )                  
    def valid_date(self,s):
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            return False

    def check_date(self,params):
        cond =[]
        if params['startDate']: 
            if self.valid_date(params['startDate']):
                cond.append(f" >= '{params['startDate']}' ")
            else: return 'Please enter startDate format YYYY-MM-DD'
        if params['endDate']:
            if self.valid_date(params['endDate']):
                cond.append(f" <= '{params['endDate']}' ")
            else: return 'Please enter endDate format YYYY-MM-DD'  
        return cond

    @jwt_required()
    def get(self):
        params = ViewDocuments.Getparser.parse_args()
        if params['limit'] < 0:
            return {
                'status':'failed',
                'message':'Invaild enter limit'
            },400
        elif params['offset'] < 0:
            return {
                'status':'failed',
                'message':'Invaild enter offset'
            },400
        if isinstance(self.check_date(params),list):
            condition=self.check_date(params)
        else:return{
            'status':'failed',
            'message':self.check_date(params)
        },400

        if params['word']:
            print('Send search keyword',params['word'])
            return make_response({
                'status':'success',
                'data':DocumentModel.search_doc_by_key(params['word'],params['limit'],params['offset'],condition) 
            },200)
        else:
            print('Not Send search keyword')
            return make_response({
                'status':'success',
                'data': DocumentModel.list_doc(params['limit'],params['offset'],condition)},200)

class ViewDocumentDetail(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('documentId',
                        type=int,
                        required=True,
                        help="This limit cannot be blank.",
                        location='args')
    @jwt_required()
    def get(self):
        claims = get_jwt()
        params=ViewDocumentDetail.parser.parse_args()
        id=params['documentId']
        doc=DocumentModel.find_doc_by_id(id)
        if doc !=None:
            loc=LocModel()
            dict_loc={'documentId':id,'userId':claims['sub'],'action':'View document detail','userAgent':request.headers.get('User-Agent'),'dateUpdate':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            print('header: ',request.headers)
            for i in dict_loc:
                setattr(loc,i,dict_loc[i])
            #print(loc.json())
            loc.save_to_db()
            return make_response({'status':'success',
                            'data':doc.json(DocumentModel.find_signature_in_doc(id))},200)
        else: return {'status': 'failed',
                      'message': 'Document not Found'},404

    @jwt_required()
    def put(self):
        claims = get_jwt()
        if not claims['is_admin']:
            return {
                'status':'failed',
                'message': 'Admin privilege required'},403
        saveparser = reqparse.RequestParser()
        saveparser.add_argument('documentId',
                            type=int,
                            required=True,
                            help="This field cannot be blank."
                            )
        saveparser.add_argument('sendAddress',
                            type=str,
                            required=True,
                            location='json',
                            help="This field cannot be blank."
                            )
        saveparser.add_argument('receiver',
                            type=str,
                            required=True,
                            location='json',
                            help="This field cannot be blank."
                            )
        saveparser.add_argument('title',
                            type=str,
                            required=True,
                            location='json',
                            help="This field cannot be blank."
                            )
        saveparser.add_argument('signature',
                            type=list,
                            required=True,
                            location='json',
                            help="This field cannot be blank."
                            )
        saveparser.add_argument('dateWrite',
                            type= str,
                            required=True,
                            location='json',
                            help="This field cannot be blank."
                            )
        params=ViewDocumentDetail.parser.parse_args()
        Data = saveparser.parse_args()
        id=params['documentId']
        doc=DocumentModel.find_doc_by_id(id)
        if params['documentId'] != Data['documentId'] and DocumentModel.find_doc_by_id(Data['documentId']):
            return {
                'status':'success',
                'message':'A document with that documentId already exists'
            },400 
        for i in Data:
            value=Data[i]
            if i =='dateWrite':
                value=datetime.strptime(Data[i],"%a, %d %b %Y %H:%M:%S %Z").date()
            setattr(doc,i,value)
        doc.update_db()
        loc=LocModel()
        dict_loc={'documentId':doc.documentId,'userId':claims['sub'],'action':'Edit document','userAgent':request.headers.get('User-Agent'),'dateUpdate':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        print('dict_loc:',dict_loc)
        for i in dict_loc:
            setattr(loc,i,dict_loc[i])
        loc.save_to_db()
        return make_response({
            'status':'success',
            'data': doc.json(Data['signature'])
        },200)

    @jwt_required()
    def delete(self):
        claims = get_jwt()
        if not claims['is_admin']:
            return {
                'status':'failed',
                'message': 'Admin privilege required'},403
        params=ViewDocumentDetail.parser.parse_args()
        id=params['documentId']
        DocumentModel.delete_doc(id)
        loc=LocModel()
        dict_loc={'documentId':id,'userId':claims['sub'],'action':'Delete document','userAgent':request.headers.get('User-Agent'),'dateUpdate':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        for i in dict_loc:
            setattr(loc,i,dict_loc[i])
        loc.save_to_db()
        return {'status': 'success',
                'data':'Delete complete'},200






