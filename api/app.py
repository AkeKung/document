from flask import Flask,jsonify
from flask_restful import Api,Resource
from flask_jwt_extended import JWTManager,jwt_required,create_access_token,get_jwt,get_jwt_identity
from blacklist import BLACKLIST
from authen import UserRegister,UserLogin,UserLogout,ResetPassword,ForgetPassword
from user import UserModel,UserProfile,ManageUser,ViewManageUser
from extract import Extract
from upload import Upload
from history import ViewLoc,GetStats
from document import ViewDocuments,ViewDocumentDetail,ViewPages
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv(".env")
# sp = SparkPost(os.getenv('SPARKPOST_API_KEY'))

app=Flask(__name__)
app.config['PROPAGATE_ExCEPTIONS'] = True
app.config['JWT_BLACKLIST_ENABLED'] =True
app.config['JWT_BLACKLIST_TOKEN_CHECK']=['access','refresh']

# app.config['MAIL_SERVER']= "smtp.gmail.com"
# app.config['MAIL_PORT']= 465
# app.config['MAIL_USERNAME']= os.getenv('EMAIL_USER')
# app.config['MAIL_PASSWORD']= os.getenv('EMAIL_PASS')
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True



app.secret_key='jose'
api = Api(app)

jwt=JWTManager(app)
#mail=Mail(app)

@jwt.additional_claims_loader
def add_claims_to_jwt(identity):
    user = UserModel.find_by_id(identity)
    #print("Permiss: ",identity)
    if user.permiss=="admin": 
        return {'is_admin':True}
    else: 
        return {'is_admin':False}

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(decrypted_type,decrypted_token):
    #print("decrypted_type: ",decrypted_type," decrypted_token:",decrypted_token)
    return  decrypted_token['jti'] in BLACKLIST

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'status':'failed',
        'message':{
            'description':'The token has expired',
            'error': 'token_expired'
        }
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'status':'failed',
        'message':{
            'description':'Signature verification failed',
            'error': 'invalid_token'
        }
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'status':'failed',
        'message':{
            'description':'Request does not contain an access token',
            'error': 'authorization_required'
            }
    }), 401

@jwt.needs_fresh_token_loader
def token_not_fresh_callback():
    return jsonify({
        'status':'failed',
        'message':{
            'description':'The token is not fresh',
            'error': 'fresh_token_required'
        }
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'status':'failed',
        'message':{
            'description':'The token has been revoked',
            'error': 'token_revoked'
        }
    }), 401

class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user=get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False,expires_delta=timedelta(hours=1))
        return {
            'status':'success',
            'data':{
                'access_token':new_token
                }
            },200

api.add_resource(UserRegister, '/authen/register')
api.add_resource(UserLogin,'/authen/login')
api.add_resource(UserLogout,'/authen/logout')
api.add_resource(ResetPassword,'/authen/resetPassword/<token>')
api.add_resource(ForgetPassword,'/authen/forget')
api.add_resource(UserProfile,'/account/profile')
api.add_resource(ViewLoc,'/account/history')
api.add_resource(GetStats,'/account/history/stats')
api.add_resource(ViewManageUser,'/account/manage')
api.add_resource(ManageUser,'/account/manage/')
api.add_resource(Upload,'/upload')
api.add_resource(TokenRefresh,'/refresh')
api.add_resource(Extract,'/upload/extract')
api.add_resource(ViewDocuments,'/list/documents')
api.add_resource(ViewDocumentDetail,'/list/documents/')
api.add_resource(ViewPages,'/list/documents/pages')

if __name__ == '__main__':
    app.run(port=5000,debug=True)