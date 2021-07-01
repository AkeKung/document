from datetime import datetime,timedelta
from flask import make_response
from flask_restful import Resource
import mysql.connector,os
from flask_restful import Resource,reqparse
from flask_jwt_extended import jwt_required,get_jwt
import werkzeug,re
from werkzeug.security import check_password_hash, generate_password_hash
from firebase import storage 


class UserModel:

    def __init__(self,username,email,password,_id =-1,tname = None,fname = None,lname = None,permiss="user",picture = None,status="off",lastConnect=None):
        self.userId      =   _id
        self.username    =   username
        self.tname       =   tname
        self.fname       =   fname
        self.lname       =   lname
        self.email       =   email
        self.password    =   password
        self.permiss     =   permiss
        self.picture     =   picture
        self.status      =   status
        self.lastConnect =   lastConnect

    def json(self):
        return {"userId":self.userId,
                "username":self.username,
                "tname":self.tname,
                "fname":self.fname,
                "lname":self.lname,
                "email":self.email,
                "password":self.password,
                "permiss":self.permiss,
                "picture":self.picture,
                "status":self.status,
                "lastConnect":self.lastConnect
                }

    def get_manage(self):
        return {"userId":self.userId,
                "username":self.username,
                "email":self.email,
                "picture":self.picture,
                "permiss":self.permiss,
                "status":self.status,
                "lastConnect":self.lastConnect
                }
    
    def save_to_db(self):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query = "INSERT INTO user (username, email, password, permiss ,status) VALUES (%s ,%s,%s,%s,%s)"
        mycursor.execute(query,(self.username, self.email, self.password,self.permiss,self.status))
        mydb.commit()
        mydb.close()

    def update_to_db(self):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query = "UPDATE user SET username = %s, tname = %s, fname = %s, lname = %s, email = %s, password = %s, permiss = %s, picture= %s, status = %s ,last_connect = %s WHERE u_id = %s"
        mycursor.execute(query,(self.username, self.tname, self.fname, self.lname, self.email, self.password,self.permiss,self.picture,self.status, self.lastConnect,self.userId))
        mydb.commit()
        mydb.close()

    @classmethod
    def find_by_user(cls, user,type):
        #return cls.query.filter_by(username=username).first()
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query = f"SELECT * FROM user WHERE {type}"+" = (%s)"
        mycursor.execute(query, (user,))
        result = mycursor.fetchone()
        mydb.close()
        if result:
            #print(result)
            user= cls(_id=int(result[0]),username=result[1],tname=result[2],fname=result[3],lname=result[4],email=result[5],password=result[6],permiss=result[7],picture=result[8],status=result[9],lastConnect=result[10])
        else:
            user=None
        #mydb.close()
        return user
    
    @classmethod
    def find_by_id(cls, _id):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query = "SELECT * FROM user WHERE u_id= (%s)"
        mycursor.execute(query, (_id,))
        result = mycursor.fetchone()
        mydb.close()
        if result:
            #print(result)
            user= cls(_id=int(result[0]),username=result[1],tname=result[2],fname=result[3],lname=result[4],email=result[5],password=result[6],permiss=result[7],picture=result[8],status=result[9],lastConnect=result[10])
        else:
            user=None
        #mydb.close()
        return user

    @classmethod
    def get_user(cls,limit,offset,cond):
        text=''
        if cond:
            if len(cond) ==1:
                text+=f'where last_connect {cond[0]}'
            elif len(cond)==2:
                text+=f'where last_connect {cond[0]} and last_connect {cond[1]}'
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor =  mydb.cursor()
        query = "SELECT * FROM user {2} order by last_connect DESC limit {0} offset {1}".format(limit,offset,text)
        mycursor.execute(query)
        result = mycursor.fetchall()
        mydb.close()
        list=[]
        for i in result:
            user= cls(_id=int(i[0]),username=i[1],tname=i[2],fname=i[3],lname=i[4],email=i[5],password=i[6],permiss=i[7],picture=i[8],status=i[9],lastConnect=i[10])
            list.append(user.get_manage())
        return list

    @classmethod
    def search_user_by_key(cls,keyword,limit,offset,cond):
        text=''
        if cond:
            if len(cond) ==1:
                text+=f'and last_connect {cond[0]}'
            elif len(cond)==2:
                text+=f'and last_connect {cond[0]} and last_connect {cond[1]}'
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor =  mydb.cursor()
        query ="""
        select * from user where (u_id like '%{0}%' or username like '%{0}%' or tname like '%{0}%' or fname like '%{0}%' or lname like '%{0}%' or email like '%{0}%' or permiss like '%{0}%' or status like '%{0}%' or last_connect like '%{0}%' ) {3}
        order by last_connect DESC limit {1} offset {2};
        """.format(keyword,limit,offset,text) 
        #print(query)
        mycursor.execute(query) 
        result = mycursor.fetchall()
        mydb.close()
        list=[]
        for i in result:
            user= cls(_id=int(i[0]),username=i[1],tname=i[2],fname=i[3],lname=i[4],email=i[5],password=i[6],permiss=i[7],picture=i[8],status=i[9],lastConnect=i[10])
            list.append(user.get_manage())
        return list

regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'

class UserProfile(Resource):
    
    @jwt_required()
    def get(self):
        user=UserModel.find_by_id(get_jwt()['sub'])
        if user:
            return make_response({'status':'success',
                    'data':{
                        "userId":user.userId,
                        "username":user.username,
                        "tname":user.tname,
                        "fname":user.fname,
                        "lname":user.lname,
                        "email":user.email,
                        "permiss":user.permiss,
                        "picture":user.picture,
                        "status":user.status
                    }},200)
        #print(user.json())
        return {'status':'failed',
                'message': "the user doesn't exist"},400

    @jwt_required()
    def put(self):
        profileParser = reqparse.RequestParser()
        profileParser.add_argument('username',type=str)
        profileParser.add_argument('tname',type=str)
        profileParser.add_argument('fname',type=str)
        profileParser.add_argument('lname',type=str)
        profileParser.add_argument('email',type=str)
        profileParser.add_argument('password',
                                    type=str,
                                    required=True,
                                    help="This field cannot be blank."
                                    )
        user=UserModel.find_by_id(get_jwt()['sub'])
        if user:
            data = profileParser.parse_args()
            if not re.search(regex, data['email']):
                    return {'status':'failed',
                            "message": "Invalid Email"}, 400

            if UserModel.find_by_user(data['username'],'username') and user.username != data['username']:
                    return {'status':'failed',
                            'message': "A user with that username already exists"},400

            if UserModel.find_by_user(data['email'],'email') and user.email != data['email']:
                    return {'status':'failed',
                            'message': "A user with that email already exists"},400
            if check_password_hash(user.password,data['password']):
                user.username=data['username']
                user.tname=data['tname']
                user.fname=data['fname']
                user.lname=data['lname']
                user.email=data['email']
                user.update_to_db()
                edit={}
                for key,value in data.items():
                    if key != 'password':
                        edit[key]=value
                return {'status':'success',
                        'data': edit
                },200
            else:
                return  {'status':'failed',
                        'message': "Password incorrect"},400
        else:
            return {'status':'failed',
                    'message': "the user doesn't exist"},400

    @jwt_required()
    def post(self):
        pictureParser = reqparse.RequestParser()
        pictureParser.add_argument('picture',
                                    type=werkzeug.datastructures.FileStorage,
                                    location='files',
                                    required=True,
                                    help="This field cannot be blank."
                                    )

        Data = pictureParser.parse_args()
        if not Data['picture']:
            return {
                'status':'failed',
                'message': 'This field cannot be blank.'},400
        user=UserModel.find_by_id(get_jwt()['sub'])
        path_local="profile/{}.png".format(user.userId)
        Data['picture'].save(path_local)
        path_on_cloud = "profile/{}".format(user.userId)
        upload=storage.child(path_on_cloud).put(path_local)
        url=storage.child(path_on_cloud).get_url(upload['downloadTokens'])
        user.picture=url
        user.update_to_db()
        return {
                'status':'success',
                'data': user.picture}

class ManageUser(Resource):                           
    parser = reqparse.RequestParser()
    parser.add_argument('userId',
                            type=int,
                            required=True,
                            help="This field cannot be blank.",
                            location='args'
                            )
    Editparser = reqparse.RequestParser()
    Editparser.add_argument('permiss',
                            type=str,
                            required=True,
                            help="This field cannot be blank.")
    Editparser.add_argument('email',
                            type=str,
                            required=True,
                            help="This field cannot be blank.")
    Editparser.add_argument('username',
                            type=str,
                            required=True,
                            help="This field cannot be blank.")
    Editparser.add_argument('status',
                            type=str,
                            required=True,
                            help="This field cannot be blank.")
    Editparser.add_argument('userId',
                            type=int,
                            required=True,
                            help="This field cannot be blank.")
    Editparser.add_argument('password',type=str)
    Editparser.add_argument('passwordConfirm',type=str)
    # Editparser.add_argument('passwordAdmin',
    #                         type=int,
    #                         required=True,
    #                         help="This field cannot be blank.")


    @jwt_required()
    def get(self):
        claims = get_jwt()
        if not claims['is_admin']:
            return {
                'status': 'failed',
                'message': 'Admin privilege required'},403
        params = ManageUser.parser.parse_args()
        if params['userId']:
            user=UserModel.find_by_id(params['userId'])
            if user:
                return make_response({
                'status' : 'succuess',
                'data': user.get_manage()
            },200)    


    @jwt_required()
    def put(self):
        claims = get_jwt()
        if not claims['is_admin']:
            return {
                'status': 'failed',
                'message': 'Admin privilege required'},403
        params=ManageUser.parser.parse_args()
        data = ManageUser.Editparser.parse_args()
        user=UserModel.find_by_id(params['userId'])
        if not re.search(regex, data['email']):
                    return {'status':'failed',
                            "message": "Invalid Email"}, 400

        if UserModel.find_by_user(data['username'],'username') and user.username != data['username']:
                    return {'status':'failed',
                            'message': "A user with that username already exists"},400

        if UserModel.find_by_user(data['email'],'email') and user.email != data['email']:
                    return {'status':'failed',
                            'message': "A user with that email already exists"},400
        #print(user.json())
        for i in data:
            if i != 'userId' and i != 'passwordConfirm':
                if i=='password':
                    if data[i] == None: continue
                    if data[i] == data['passwordConfirm']:
                        setattr(user,i,generate_password_hash(data[i],method='sha256'))
                    else:
                        return {
                        'status':'failed',
                        "message": " Password not match"}, 400
                else:
                    #print(i)
                    setattr(user,i,data[i])
        user.update_to_db()
        return make_response({'status':'success',
                'data': user.get_manage()
                },200)

class ViewManageUser(Resource):

    paramsparser = reqparse.RequestParser()
    paramsparser.add_argument('limit',
                            type=int,
                            required=True,
                            help="This limit cannot be blank.",
                            location='args')
    paramsparser.add_argument('offset',
                            type=int,
                            required=True,
                            help="This field cannot be blank.",
                            location='args'
                            )
    paramsparser.add_argument('word',
                            type=str,
                            location='args'
                            )    
    paramsparser.add_argument('startDate',
                            type=str,
                            location='args'
                            )   
    paramsparser.add_argument('endDate',
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
                cond.append(f" >= '{str(self.valid_date(params['startDate']))}' ")
            else: return 'Please enter startDate format YYYY-MM-DD'
        if params['endDate']:
            if self.valid_date(params['endDate']):
                cond.append(f" <= '{str(self.valid_date(params['endDate'])+timedelta(days=1))}' ")
            else: return 'Please enter endDate format YYYY-MM-DD'
        return cond


    @jwt_required()
    def get(self):
        claims = get_jwt()
        if not claims['is_admin']:
            return {
                'status': 'failed',
                'message': 'Admin privilege required'},403
        params = ViewManageUser.paramsparser.parse_args()
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
                'data':UserModel.search_user_by_key(params['word'],params['limit'],params['offset'],condition)
        },200)
        else:
            print('Not Send search word')
            return make_response({
                'status':'success',
                'data':UserModel.get_user(params['limit'],params['offset'],condition)
        },200)