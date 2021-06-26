#from numpy.lib.function_base import extract
from document import DocumentModel
from history import LocModel
from firebase import storage
from person import PersonModel 
import mysql.connector,time,os

from flask import make_response,request
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required,get_jwt
import cv2,easyocr
import numpy as np
from datetime import datetime
from pythainlp import spell
from pythainlp.spell import NorvigSpellChecker
from itertools import chain
from collections import Counter
from skimage import morphology,img_as_float
reader = easyocr.Reader(['th','en'],recog_network = 'thai_g1')

class Extract(Resource):

    def __init__ (self):
        
        self.keyword ={
            "documentId": None,
            "title": None,
            "sendAddress": None,
            "receiver": None,
            "dateWrite": None,
            "signature": None,
        }
    
    @classmethod
    def load_setting(cls):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM keyword_setting")
        load_setting = mycursor.fetchall()
        mydb.close()
        dict={}
        for i in load_setting:
            if i[3] not in dict:
                dict[i[3]]= []
            dict[i[3]].append(i[2])
        return dict

    def divide_img(self,orderPage):
        set={orderPage[0],orderPage[-1]}
        img=list(set)
        #print('img:',img)
        page=[]
        for i in range(len(img)):
            temp_img=cv2.imread(f"temp/{img[i]}.png")  
            scale_percent = 80 # percent of original size
            width = int(temp_img.shape[1] * scale_percent / 100)
            height = int(temp_img.shape[0] * scale_percent / 100)
            dim = (width, height)
    
         # resize image
            rtemp_img = cv2.resize(temp_img, dim, interpolation = cv2.INTER_AREA)
            if len(img) == 1:
                page.append(rtemp_img[int(height/2):height, 0:width])
            if i ==0:
                page.insert(0,rtemp_img[0:int(height/3), 0:width])
            else:
                page.append(rtemp_img[int(height/3):height,0:width])
        return page

    def read_data(self,orderPage):
        #select only head and end page
        imgs=self.divide_img(orderPage)
        opt_imgs=[]
        text=[]
        for i in imgs:
            gray = cv2.cvtColor(i,cv2.COLOR_BGR2GRAY)
            #ret, bw_img = cv2.threshold(gray,2,255,cv2.THRESH_BINARY)
            #cv2.imwrite('binary'+str(i)+'.png',bw_img)
            kernel = np.ones((3,3), np.uint8)
            img_dilation = cv2.erode(gray,kernel,iterations = 1)
            opt_imgs.append(img_dilation)
            text.append(reader.readtext(img_dilation))
        return [text[0],text[1],imgs[0],imgs[1]]#opt_imgs[0],opt_imgs[1]]

    def float_sort(self,img):
        floats=[]
        imgs=[]
        for i in img: 
            if(isinstance(i[0][0][0],float)):
                floats.append(i)
            else: 
                imgs.append(i)
        for j in range(len(floats)):
            avg=[sum(idx)/4 for idx in zip(*floats[j][0])]
            #print(floats[j][1],avg)
            for i in range(len(imgs)-1):
                #print(imgs[i][0][1],avg,imgs[i+1][0][-1],imgs[i][1])
                if imgs[i][0][1][1] < avg[1] < imgs[i+1][0][-1][1]:
                    if imgs[i][0][1][0] < avg[0] < imgs[i+1][0][-1][0]:
                #if(imgs[i][0][1][0] < avg[0] < imgs[i+1][0][-1][0] and imgs[i][0][1][1] < avg[1] < imgs[i+1][0][-1][1]): 
                        #print('Yes')
                        imgs.insert(i+1,floats[j])
                        break
                    elif imgs[i][0][1][0] < avg[0] and avg[1]< imgs[i+1][0][-1][1]-100:
                        #print('Yes')
                        imgs.insert(i+1,floats[j])
                        break
        return imgs
    
    def summarize(self,position):
        x=[]
        y=[]
        for i in position:
            x1,y1=[max(idx) for idx in zip(*i)]
            x2,y2=[min(idx) for idx in zip(*i)]
            x.append(x1)
            x.append(x2)
            y.append(y1)
            y.append(y2)
        #print(x,y)
        return [int(min(y)),int(max(y)),int(min(x)),int(max(x))]
    
    def convert_date(self,date):
        MONTHS = ["มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน","กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม",]
        thainum=["๐","๑","๒","๓","๔","๕","๖","๗","๘","๙"]
        mdate=date.replace('เดือน','').replace('ปี','').split()
        print(mdate)
        if(mdate[2][0] in thainum):
            year=int(''.join(map(str, [thainum.index(i) for i in list(mdate[2])]))) -543
            day=int(thainum.index(mdate[0]))
        else:
            year=int(mdate[2].replace('พ.ศ.','').replace('ค.ศ.',''))-543 
            day=int(''.join([thainum.index(i) if i in thainum else i for i in mdate[0]]))
        m=0
        for i in range(len(MONTHS)):
            m+=1 
            if MONTHS[i] in spell(mdate[1]):break
        return datetime.strptime(str(year)+' '+str(m)+' '+str(day), '%Y %m %d').date()
    
    @classmethod
    def check_setting(self,input,setting):
        for i,j in setting.items():
            for key in j:
                if len(key) > len(input):
                    continue
                if key in input:
                    if input.strip().index(key)==0:
                        return i
        return False

    def classify_keyword(self,head,signature,img_sign):
        h_state=''
        title=''
        y=0
        x=0
        setting=self.load_setting()
        for i in range(len(head)): 
            type=self.check_setting(head[i][1],setting) 
            #y_check=(head[i][0][0][1]+head[i][0][2][1])/2
            #print(f'type: {type} data: {head[i][1]} pre(h_state): {h_state} title: {title} ' )
            if type:
                #print('now:',h_state )
                setting.pop(type,None)
                #y=y_check
                if title:
                    self.keyword[h_state]=title.strip()
                    title=''
                h_state=type
                temp=head[i][1].split()
                if type== 'dateWrite':
                    if len(temp) > 1:
                        day=[]
                        for j in temp[1:]:
                            day.append(j)
                        self.keyword[type]=self.convert_date(' '.join(day))
                    else:
                        self.keyword[type]=self.convert_date(head[i+1][1]+' '+head[i+2][1])
                        h_state=''
                    type=False
                elif len(temp) > 1:
                    title+=head[i][1].replace(type,'').strip()
                if i ==len(head)-1:
                    if type and title:
                        self.keyword[type]=title.strip()
                    break
                elif i < len(head)-1:
                    continue
            if h_state: #and ((y > y_check+10 or y < y_check+10) or (type== 'title' and )):
                #y=y_check
                title+=' '+head[i][1].strip() 

        #print(self.keyword)
        sign_sort=self.float_sort(signature)
        e_state=0
        sign=[]
        p=[]
        p_signature=[]
        for i in range(len(sign_sort)-1,-1,-1):
            type=self.check_setting(sign_sort[i][1],setting)
            text=sign_sort[i][1].strip()
            #print('text:',sign_sort[i][1],'e_state:',e_state)
            if text[-1] ==')' or e_state == 3:
                if e_state !=0:
                    #print('text:{} name:{} role:{}'.format(sign_sort[i][1],name,role))
                    #print('collect sign:{}'.format(sign))
                    if name and role:
                        sign.insert(0,[("".join(role)),(" ".join(name).strip())[1:-1]])
                        p.insert(0,[self.summarize(p_role),self.summarize(p_name)])
                        p_signature.insert(0,[self.summarize(p_role),self.summarize(p_name)])
                e_state=1
                name=[]
                role=[]
                p_name=[]
                p_role=[]
            if e_state==1:
                p_name.insert(0,sign_sort[i][0])
                #print([correct(i) for i in deepcut.tokenize(sign_sort[i][1])])
                #print('e_state: ',e_state,'text:',text,' next: ',sign_sort[i-1][1] ,' check: ',self.check_setting(sign_sort[i-1][1],setting))
                if(text[0] == '(' or self.check_setting(sign_sort[i-1][1],setting)):
                    name.insert(0,text)
                    e_state =2
                    continue
                else:
                    name.insert(0,spell(text)[0])
            elif  e_state==2:
                #print('e_state: ',e_state,'text:',text,' next: ',sign_sort[i-1][1] ,' check: ',self.check_setting(sign_sort[i-1][1],setting))
                if type=='endpoint':
                    if (self.check_setting(sign_sort[i-1][1],setting)=='signature'):
                        p_signature.append([self.summarize([sign_sort[i-1][0]])])
                    p_role.insert(0,sign_sort[i][0])
                    role.insert(0,text)
                    p.insert(0,[self.summarize(p_role),self.summarize(p_name)])
                    p_signature.insert(0,[self.summarize(p_role),self.summarize(p_name)])
                    sign.insert(0,[("".join(role)),(" ".join(name).strip())[1:-1]])
                    if (self.summarize(p_role))[0] - self.summarize([sign_sort[i-1][0]])[1] > 50:p.insert(0,[self.summarize([sign_sort[i-1][0]])[1]])
                    elif (self.summarize(p_role))[0] - self.summarize([sign_sort[i-2][0]])[1] > 50:p.insert(0,[self.summarize([sign_sort[i-2][0]])[1]])                                    
                    break
                if type =='signature':
                    p_signature.append([self.summarize([sign_sort[i][0]])])
                    e_state==3
                    continue
                if type=='personRole':
                    p_role.insert(0,sign_sort[i][0]) 
                    role.insert(0,spell(text)[0])
        # print('result signature:',sign)
        key_signature=[]

        eximg_sign=self.extract_sign(self.delect_text(img_sign,p_signature),p)
        for i in range(len(eximg_sign)):
            person=PersonModel.tokenization_name(sign[i][1])
            # print('person: ',sign[i][1],' after token: ',person)
            if len(person) == 3:
                id=PersonModel.check_person(person[0],person[1],person[2])
                if not id:
                    # print('not have')
                    id =PersonModel.current_person()+i
            else:
                id=PersonModel.current_person()+i
            key_signature.append({
                    "personId":id,
                    "personName":sign[i][1],
                    "personRole":sign[i][0],
                    "signatureImg":self.save_signature(self.keyword['documentId'],i,eximg_sign[i])
                    }) 
        self.keyword['signature']=key_signature
        return self.keyword

    def save_signature(self,documentId,i,img_sign):
        cv2.imwrite('temp/sign_'+str(i)+'.png',img_sign)
        path_on_cloud = "document/{}/{}".format(documentId,'sign_'+str(i)+'.png')
        upload=storage.child(path_on_cloud).put('temp/sign_'+str(i)+'.png')
        url=storage.child(path_on_cloud).get_url(upload['downloadTokens'])
        return url
    
    def delect_text(self,img,position_text_around_sign):
        test=img.copy()
        #print('position_text_around_sign: ',position_text_around_sign)
        for i in position_text_around_sign:
            for j in i:
                y1,y2,x1,x2,=j
                for k in range(y1,y2):
                    for l in range(x1,x2):test[k][l]=255 
        #cv2.imwrite('test.png',test)
        return test

    def extract_sign(self,img_sign,add_sign):
        s=[]
        for i in range(len(add_sign)-1): 
            if(isinstance(add_sign[i][0],int)):
                #sign=img_sign[add_sign[i][0][1]:add_sign[i+1][2][0],add_sign[i+1][0][3]:add_sign[i+1][1][2]].copy()
                sign=img_sign[add_sign[i][0]:add_sign[i+1][1][0],add_sign[i+1][1][2]:add_sign[i+1][1][3]].copy()
            else:
                #sign=img_sign[add_sign[i][2][1]:add_sign[i+1][2][0],add_sign[i+1][0][3]:add_sign[i+1][1][2]].copy()
                sign=img_sign[add_sign[i][0][1]:add_sign[i+1][1][0],add_sign[i+1][1][2]:add_sign[i+1][1][3]].copy()
            gray = cv2.cvtColor(sign,cv2.COLOR_BGR2GRAY)
            image = img_as_float(gray)
            image_binary = image < 0.5
            out_skeletonize = morphology.skeletonize(image_binary)
            temp=[]
            w=len(sign)
            h=len(sign[0])
            for i in range(w):
                row=[]
                for j in range(h):
                    if out_skeletonize[i][j]:
                        row.append(255)
                    else:row.append(0)
                temp.append(row)
            data=np.array(temp,dtype=np.uint8)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            num_labels, labels_im = cv2.connectedComponents(thresh)
            binaryImageClone = np.copy(labels_im)
            common=Counter(chain.from_iterable(binaryImageClone))
            #label=draw_label(binaryImageClone)
            
            kernel = np.ones((2,2), np.uint8)
            img_dilation = cv2.dilate(thresh, kernel, iterations=1)
            lines = cv2.HoughLinesP(data, 1, np.pi/360, 20, minLineLength=200, maxLineGap=100)
            #print('start',len(sign))
            e=[]
            l=[]
            #print('line: ',lines,' type:',type(lines))
            if isinstance(lines,np.ndarray):
                for line in lines:
                    row=[]
                    for x1,y1,x2,y2 in line:
                        #print(x1,y1,x2,y2)
                        m = (y2 - y1) / (x2 - x1)
                        c = y1 - m* x1
                        row.append([m,c])
                        for i in range(0,len(data[0])):
                            if(int(m*i+c) < len(gray) and m*i+c >=0):
                                if(labels_im[int(m*i+c)][i] != 0): l.append(labels_im[int(m*i+c)][i])
                    e.append(row)
                    label_del= list(set(l))
                    kernel = np.ones((5,5), np.uint8)
                    img_dilation = cv2.dilate(gray, kernel, iterations=1)
                    for m in range(len(gray)):
                        for n in range(len(gray[0])):
                            if( labels_im[m][n] in label_del and common[labels_im[m][n]] < w*h/1000 ):
                                gray[m][n]=255
                    kernel = np.ones((3,3), np.uint8)
                    img_dilation = cv2.dilate(gray, kernel, iterations=1) 
                    img_erosion = cv2.erode(img_dilation, kernel, iterations=1)
                s.append(img_erosion)
        return s

    @jwt_required()
    def put(self):
        Extractparser = reqparse.RequestParser()
        Extractparser.add_argument('documentId',
                            type=int,
                            required=True,
                            help="This field cannot be blank."
                            )
        Extractparser.add_argument('pages',
                            type=list,
                            required=True,
                            location='json',
                            help="This field cannot be blank."
                            )
        claims = get_jwt()
        if not claims['is_admin']:
            return {'message': 'Admin privilege required'},403
        Data = Extractparser.parse_args()
        orderPage=[]
        for i in Data['pages']:
            for j,k in i.items():
                orderPage.append(int(j))
                DocumentModel.save_page(Data['documentId'],int(j),k)
        self.keyword['pageSequence']=orderPage
        self.keyword['documentId']=Data['documentId']
        start_time = time.time()
        head,signature,img_head,img_sign=self.read_data(orderPage)
        print ("extract time --- %s seconds ---" % (time.time() - start_time))
        # print('head: ')
        # for i in head:
        #     print (i)
        # print('signature:')
        # for i in signature:
        #     print(i)
        start_time=time.time()
        result=self.classify_keyword(head,signature,img_sign)
        print ("classify_keyword time --- %s seconds ---" % (time.time() - start_time))
        self.save_pre_to_db() 
        return make_response({
            'message': 'success',
            'data': self.keyword
        },200)
    
    def save_pre_to_db(self):
        mycursor = mydb.cursor()
        sql = 'insert into document (documentId,p_title,p_sendAddress,p_receiver,pageSequence) value (%s,%s,%s,%s,%s)'
        val=(self.keyword['documentId'],self.keyword['title'],self.keyword['sendAddress'],self.keyword['receiver'],str(self.keyword['pageSequence']))
        mycursor.execute(sql,val)
        mydb.commit()
        # for i in self.keyword['signature']:
        #     self.save_to_signature(i)

    def save_to_signature(self,signature):
        person=PersonModel()
        id_person=person.save_person(signature['personName'])
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        sql = "INSERT INTO signature (id_signature,doc_id,person_id,signature_role,signature_img) VALUES (%s,%s,%s,%s,%s)"
        val = (DocumentModel.current_page()+1,self.keyword['documentId'],id_person,signature['personRole'],signature['signatureImg'])
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()

    @jwt_required()
    def post(self):
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
        saveparser.add_argument('pageSequence',
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
        Data = saveparser.parse_args()
        doc=DocumentModel()
        for i in Data:
            value=Data[i]
            if i =='dateWrite':
                value=datetime.strptime(Data[i],"%a, %d %b %Y %H:%M:%S %Z").date()
            #if i =='pageSequence':page
            setattr(doc,i,value)
        doc.save_to_db()
        loc=LocModel()
        time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dict_loc={'documentId':doc.documentId,'userId':claims['sub'],'action':'Insert document','userAgent':request.headers.get('User-Agent'),'dateUpdate':time}
        for i in dict_loc:
            setattr(loc,i,dict_loc[i])
        loc.save_to_db()
        for f in os.listdir('temp/'):
            os.remove(os.path.join('temp/', f))
        setattr(doc,'dateUpdate',time)
        return make_response({
            'status':'success',
            'data': doc.json(DocumentModel.find_signature_in_doc(doc.documentId)) 
        },200)
