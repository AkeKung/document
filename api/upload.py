from flask.helpers import make_response
from pdf2image import convert_from_path,convert_from_bytes
from flask import jsonify 
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required,get_jwt
from firebase import storage 
import werkzeug
from document import DocumentModel

class Upload(Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('file',
                        type=werkzeug.datastructures.FileStorage,
                        location='files',
                        required=True,
                        action='append',
                        )

    def save_to_firebase(self,file,documentId,filename):
        path_local='temp/'+filename
        file.save(path_local)
        path_on_cloud = "document/{}/{}".format(documentId,filename)
        upload=storage.child(path_on_cloud).put(path_local)
        url=storage.child(path_on_cloud).get_url(upload['downloadTokens'])
        return url

    def validation_upload(self,data):
        all_type={'image/png','application/pdf','image/jpeg'}
        type={i.mimetype for i in data['file']}
        if '' in type:
            return {
                'status':'failed',
                'message': 'This field cannot be blank.'},400
        check=all_type.difference(type)
        if len(check) >2:
            return {
                'status':'failed',
                'message': 'Input type incorrect.'},400
        elif len(check)==1 and 'application/pdf' not in check:
            return {
                'status':'failed',
                'message': 'Input not same type.'},400
        else:
            return 0

    @jwt_required() # @jwt_required(fresh=True)
    def post(self):
        claims = get_jwt()
        if not claims['is_admin']:
            return {
                'status':'failed',
                'message': 'Admin privilege required'},403
        Data = Upload.parser.parse_args()
        #print("Data: ",Data)
        
        if self.validation_upload(Data) :
            return self.validation_upload(Data) 
        doc=DocumentModel()
        documentId=doc.current_doc()+1
        dict_file={
                    "documentId":documentId,
                    "pages":[]
            }
        j=0
        for i,data in enumerate( Data['file']):
            filename = data.filename
            filetype= data.mimetype.split("/")[-1].lower()
            #print("filetype: ",filetype)

            #convert pdf to image
            if "pdf" in filetype:
                pages = convert_from_bytes(data.stream.read(), 300)
                for page in pages:
                    #save each page
                    filename="{}.png".format(j)
                    url=self.save_to_firebase(page,documentId,filename)
                    dict_file['pages'].append({j:url})
                    j+=1
            else:
                url=self.save_to_firebase(data,documentId,filename)
                dict_file['pages'].append({j:url})
                j+=1

        return make_response({
                'status':'success',
                'data': dict_file},200)
