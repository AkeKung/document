from flask.helpers import make_response
from flask_restful import Resource,reqparse
from user import UserModel
from flask_jwt_extended import create_access_token,create_refresh_token
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import datetime,timedelta
import re,time
from blacklist import BLACKLIST
from flask_jwt_extended import jwt_required,get_jwt
from sendemail import SendEmail

# import boto3
# from botocore.exceptions import ClientError
# from flask_mail import Message
# from sparkpost import SparkPost
# from sparkpost.exceptions import SparkPostAPIException
# sp = SparkPost(os.getenv('SPARKPOST_API_KEY'))


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    parser.add_argument('password',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    parser.add_argument('email',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    parser.add_argument('passwordConfirm',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    def post(self):
        data = UserRegister.parser.parse_args()
        regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'

        if UserModel.find_by_user(data['username'],'username'):
            return {        
                'status':'failed',
                "message": "A user with that username already exists"}, 400

        elif not re.search(regex, data['email']):
            return {
                'status':'failed',
                "message": "Invalid Email"}, 400

        elif data['password'] != data['passwordConfirm']:
            return {
                'status':'failed',
                "message": " Password not match"}, 400
            

                
        hashed = generate_password_hash(data['password'],method='sha256')
        time = datetime.now()
        user = UserModel(data['username'],data['email'],hashed,_id = UserModel.current_user()+1,status="online",lastConnect=time.strftime('%Y-%m-%d %H:%M:%S'),picture="https://firebasestorage.googleapis.com/v0/b/projectdoc-5af7b.appspot.com/o/template%2FArtboard%201.png?alt=media&token=b74d1752-21ae-4255-8d37-1440d1c967d5")
        print(user.json())
        user.save_to_db()
        access_token = create_access_token(identity=user.userId, fresh=True,expires_delta=timedelta(hours=3))
        refresh_token = create_refresh_token(user.userId)
        return make_response({
            'status':'success',
            "data": {
                "userId":user.userId,
                "username":user.username,
                "permiss":user.permiss,
                "status":user.status,
                "picture":user.picture,
                "expires_token":time+timedelta(hours=3) ,
                "access_token":access_token,
                "refresh_token":refresh_token}
                }, 200)

    #resources/authen.py
class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username/email',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    parser.add_argument('password',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    def post(self):
        data = UserLogin.parser.parse_args()
        if not data['username/email'] :
            return {
                'status':'failed',
                "message": "Please Enter username/email"}, 400  
        elif not data['password'] :
            return {
                'status':'failed',
                "message": "Please Enter password"}, 400  
        regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
        if re.search(regex,data['username/email']):
            type='email'
        else:
            type='username'
        user = UserModel.find_by_user(data['username/email'],type)
        if user: 
            if check_password_hash(user.password,data['password']):
                if user.status == "suspended":
                    if user.lastConnect :
                        if datetime.now() <= user.lastConnect:
                            diff = timedelta(seconds=(user.lastConnect - datetime.now()).total_seconds())
                            t = str(diff).split(':')
                            return {
                                "status": "failed",
                                "message" : "Your account is suspended, remain time {} Hours {} Minutes {} Seconds".format(t[0],t[1],int(float(t[2]
                                )))
                                },403 
                    else :
                        return {
                            "status":"failed",
                            "message": "Your account is suspended, please contact admin." 
                        },403
                time = datetime.now()
                access_token = create_access_token(identity=user.userId, fresh=True,expires_delta=timedelta(hours=3))
                refresh_token = create_refresh_token(user.userId)
                user.status ="online"
                user.lastConnect= time.strftime('%Y-%m-%d %H:%M:%S')
                #print(user.json())
                user.update_to_db()
                return make_response({
                    'status': 'success',
                    "data":{
                        "userId":user.userId,
                        "username":user.username,
                        "permission":user.permiss,
                        "status":user.status,
                        "picture":user.picture,
                        "expires_token":time+timedelta(hours=3) ,
                        "access_token": access_token,
                        "refresh_token":refresh_token
                    }
                    },200)
            return {
                'status':'failed',
                "message": "Password incorrect"}, 400        
        else: return {
            'status':'failed',
            "message": "User does not exist"
            }, 400

class UserLogout(Resource):
    @jwt_required()
    def post(self):
        jti=get_jwt()
        BLACKLIST.add(jti['jti'])
        user=UserModel.find_by_id(jti['sub'])
        user.status ="invisible"
        user.lastConnect= datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user.update_to_db()
        #print(user.json())
        return {
            'status': 'success',
            'message': 'Successfully logged out.'
            },200

class ForgetPassword(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('email',
                        type=str,
                        required=True,
                        help="This field cannot be blank.",
                        location='args'
                        )
    def post(self):
        data=ForgetPassword.parser.parse_args()
        regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
        if re.search(regex,data['email']):
            user =UserModel.find_by_user(data['email'],'email')
        else:
            return {
                "status":"failed",
                "message": "Invalid Email"
                },400
        if user:
            token = create_access_token(identity=user.userId,fresh=True,expires_delta=timedelta(hours=4))
            endpoint=f'http://localhost:80/lisa/user/resetPassword/?token={token}'
            SendEmail.send_reset_email(user,endpoint)
            return {'status':'success',
                'data':{
                    'access_token':token
                }},200
        else:
            return {
                "status": "failed",
                "message": "There is no account with this email. You must register first."
            },400

class ResetPassword(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('password',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    parser.add_argument('passwordConfirm',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    
    @jwt_required()
    def put(self,token):
        claim=get_jwt()
        #print(claim)
        user=UserModel.find_by_id(claim['sub'])
        #print(user.json())
        data = ResetPassword.parser.parse_args()
        if data['password'] != data['passwordConfirm']:
            return {
                'status':'failed',
                "message": " Password not match"}, 400
        hashed = generate_password_hash(data['password'],method='sha256')
        setattr(user,'password',hashed)
        user.update_to_db()
        access_token = create_access_token(identity=user.userId, fresh=True,expires_delta=timedelta(hours=3))
        refresh_token = create_refresh_token(user.userId)
        return {
            "status":"success",
            "data":{
                "access_token":access_token,
                "refresh_token":refresh_token
            }
        },200