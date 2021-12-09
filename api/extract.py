#from numpy.lib.function_base import extract
from document import DocumentModel
from history import LocModel
from firebase import storage
from person import PersonModel,tname
import time,json,os,mysql.connector
#from db import mydb

from flask import make_response,request,jsonify
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required,get_jwt
import cv2,easyocr
import numpy as np
from datetime import datetime,date
from pythainlp import spell
from pythainlp.spell import NorvigSpellChecker
from itertools import chain
from collections import Counter
from skimage import morphology,img_as_float
reader = easyocr.Reader(['th','en'],recog_network = 'thai_g1', gpu=True)
MONTHS = ["มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน","กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"]
thainum={"๐":'0',"๑":'1',"๒":'2',"๓":'3',"๔":'4',"๕":'5',"๖":'6',"๗":'7',"๘":'8',"๙":'9','o':'0'}

def default(o):
    if isinstance(o, (date, datetime)):
        return o.strftime('%a, %d %b %Y 00:00:00 GMT')

def levenshteinDistanceDP(token1, token2):
        distances = np.zeros((len(token1) + 1, len(token2) + 1))

        for t1 in range(len(token1) + 1):
            distances[t1][0] = t1

        for t2 in range(len(token2) + 1):
            distances[0][t2] = t2
            
        a = 0
        b = 0
        c = 0
        
        for t1 in range(1, len(token1) + 1):
            for t2 in range(1, len(token2) + 1):
                if (token1[t1-1] == token2[t2-1]):
                    distances[t1][t2] = distances[t1 - 1][t2 - 1]
                else:
                    a = distances[t1][t2 - 1]
                    b = distances[t1 - 1][t2]
                    c = distances[t1 - 1][t2 - 1]
                    
                    if (a <= b and a <= c):
                        distances[t1][t2] = a + 1
                    elif (b <= a and b <= c):
                        distances[t1][t2] = b + 1
                    else:
                        distances[t1][t2] = c + 1
        print(token1,token2)
        return distances[len(token1)][len(token2)]

class Extract(Resource):

    def __init__ (self):
        self.keyword ={
            "documentId": None,
            "title": None,
            "sendAddress": None,
            "receiver": None,
            "dateWrite": None,
        }
        self.signature = []
    
    def load_setting(self,type):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        sql = "SELECT * FROM keyword_setting where keyword_id < 5"
        if type == 1 :
            sql = sql[:-3]+">4"
        mycursor.execute(sql)
        load_setting = mycursor.fetchall()
        mydb.close()
        dict={}
        for i in load_setting:
            if i[3] not in dict:
                dict[i[3]]= []
            dict[i[3]].append(i[2])
        return dict

    def read_data(self,type,page):
        print(page)
        temp_img=cv2.imread(f"temp/{page}.png")
        scale_percent = 80 # percent of original size
        width = int(temp_img.shape[1] * scale_percent / 100)
        height = int(temp_img.shape[0] * scale_percent / 100)
        dim = (width, height)
    
         # resize image
        rtemp_img = cv2.resize(temp_img, dim, interpolation = cv2.INTER_AREA)
        #d_img = None
        if type == 0:
            d_img=rtemp_img[0:int(height/3), 0:width]
        elif type == 1:
            #j=0
            #print(f"page:{self.read_page()}")
            #for i in self.read_page():
            #    j+=1
            if page=="0":
                d_img=rtemp_img[int(height/2):height, 0:width]
            else:
                d_img=rtemp_img[0:height,0:width]
        gray = cv2.cvtColor(d_img,cv2.COLOR_BGR2GRAY)
        #ret, bw_img = cv2.threshold(gray,2,255,cv2.THRESH_BINARY)
        #cv2.imwrite('binary'+str(i)+'.png',gray)
        kernel = np.ones((3,3), np.uint8)
        img_dilation = cv2.erode(gray,kernel,iterations = 1)
        #opt_imgs.append(img_dilation)
        return [reader.readtext(img_dilation),d_img]#opt_imgs[0],opt_imgs[1]]

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
            print(floats[j][1],avg)
            check=[]
            for i in range(len(imgs)-1):
                print(imgs[i][0][1],avg,imgs[i+1][0][-1],imgs[i][1])
                if imgs[i][0][1][1] < avg[1] < imgs[i+1][0][-1][1]:
                    if imgs[i][0][1][0] < avg[0] < imgs[i+1][0][-1][0]:
                #if(imgs[i][0][1][0] < avg[0] < imgs[i+1][0][-1][0] and imgs[i][0][1][1] < avg[1] < imgs[i+1][0][-1][1]): 
                        print('Yes')
                        imgs.insert(i+1,floats[j])
                        break
                    elif imgs[i][0][1][0] < avg[0] and avg[1]< imgs[i+1][0][-1][1]-100:
                        print('Yes')
                        imgs.insert(i+1,floats[j])
                        break
                    elif imgs[i][0][1][0] > avg[0]:
                        check.append(i+1)
            imgs.insert(min(check),floats[j])
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
        
        chance = 543
        if 'ค.ศ.' in date:
            chance = 0
        d,m,y=date.replace('เดือน','').replace('ปี','').replace('พ.ศ.','').replace('ค.ศ.','').split() 
        if y[0] in thainum : 
            year=int(''.join(map(str, [thainum[i] for i in y]))) -chance
            day=int(''.join([thainum[i] for i in d]))
        else:
            year=int(y)-chance 
            day=int(d)
        #print(f'day:{day} month: {m} year:{year}') 
        ms=0
        for i in MONTHS:
            ms+=1 
            if i in spell(m)[0]:break 
        return datetime.strptime(str(year)+' '+str(ms)+' '+str(day), '%Y %m %d').date()
    
    @classmethod
    def check_setting(cls,input,setting):
        min=[100,""]
        type=""
        for i,j in setting.items():
            for key in j:
                if len(key) > len(input):
                    continue
                distance =levenshteinDistanceDP(input,key)
                if(distance==0):
                    return i,input.replace(key,"").strip()
                elif(distance<min[0]):
                    min=[distance,input.replace(key,"").strip()]
                    type = i
        if(min[0]<2):
            return type,min[1]
        else:
            return False,""
    
    def classify_head(self,head):
        sort_head=self.float_sort(head)
        h_state=''
        title=''
        y=0
        x=0
        self.setting=self.load_setting(0)
        k=0
        for i in range(len(sort_head)): 
            type,pre_temp=self.check_setting(sort_head[i][1],self.setting)
            p=self.summarize([sort_head[i][0]])
            y_check=(p[0]+p[1])/2
            x_check=(p[2]+p[3])/2
            print(f'type: {type} data: {sort_head[i][1]} pre(h_state): {h_state} title: {title} x: {x_check} y: {y_check}' )
            if type:
                self.setting.pop(type,None)
                x=x_check
                y=y_check
                #print(f'x: {x} y: {y}' )
                if title and type != h_state:
                    if h_state == "dateWrite":
                        self.keyword[h_state]=self.convert_date(title.strip())
                    else: self.keyword[h_state]=title.strip()
                    k+=1
                    if k == 4: break
                    title=''
                h_state=type
                title+=pre_temp
                if i < len(sort_head)-1:
                    continue
            #print(h_state,"x_check: ",x_check,"x ",x ,"y_check:",y_check,"y", y)
            if h_state and ((x_check > x and abs(y-y_check)<15 ) or (x_check < x and abs(y-y_check)<80)):
                x=x_check
                y=y_check
                title+=' '+sort_head[i][1].strip() 
            if i ==len(sort_head)-1:
                if title and h_state and self.keyword[h_state]==None:
                    if h_state == "dateWrite":
                        self.keyword[h_state]=self.convert_date(title.strip())
                    else:self.keyword[h_state]=title.strip()
                break

        print("head: ", self.keyword)
        return self.keyword
        
    def classify_signature(self,signature,img_sign):
        sign_sort=self.float_sort(signature)
        self.setting=self.load_setting(1)
        e_state=0
        sign=[]
        p=[]
        p_signature=[]
        end_current=0
        count_fail=0
        for i in range(len(sign_sort)-1,-1,-1):
            type=self.check_setting(sign_sort[i][1].replace(",","").replace(".",""),self.setting)[0]
            text=sign_sort[i][1].strip()
            print('text:',sign_sort[i][1],'e_state:',e_state ," type: ",type)
            check = self.check_setting(sign_sort[i-1][1],self.setting)[0]
            if text[-1] ==')' or e_state == 3:
                if e_state !=0:
                    #print('collect sign:{}'.format(sign))
                    print(f"name {name} role {role}")
                    if name and role:
                        sign.insert(0,[("".join(role)),(" ".join(name).strip())])
                        p.insert(0,[self.summarize(p_role),self.summarize(p_name)])
                        p_signature.insert(0,[self.summarize(p_role),self.summarize(p_name)])
                        end_current=i-1
                if text[-1] ==')' :
                    e_state=1
                else: 
                    e_state=0
                name=[]
                role=[]
                p_name=[]
                p_role=[]
            if e_state==1:
                #print([correct(i) for i in deepcut.tokenize(sign_sort[i][1])])
                #print('e_state: ',e_state,'text:',text,' next: ',sign_sort[i-1][1] ,' check: ',self.check_setting(sign_sort[i-1][1],setting))
                if(text[0] == '(' or check):
                    p_name.insert(0,sign_sort[i][0])
                    name.insert(0,text.replace('(','').replace(')',''))
                    e_state =2
                    continue
                else:
                    p_name.insert(0,sign_sort[i][0])
                    name.insert(0,text.replace('(','').replace(')',''))
            elif  e_state==2:
                if type=='endpoint':
                    if (check=='signature'):
                        p_signature.append([self.summarize([sign_sort[i-1][0]])])
                    p_role.insert(0,sign_sort[i][0])
                    role.insert(0,text.replace(",","").replace(".",""))
                    p.insert(0,[self.summarize(p_role),self.summarize(p_name)])
                    p_signature.insert(0,[self.summarize(p_role),self.summarize(p_name)])
                    j=0
                    while self.summarize(p_role)[0] - self.summarize([sign_sort[i-j][0]])[1] < 50:
                        j+=1
                        if sign_sort[i-j][1].strip() in tname:
                            name.insert(0,sign_sort[i-j][1].strip())
                    p.insert(0,[self.summarize([sign_sort[i-j][0]])[1]])
                    sign.insert(0,[("".join(role)),(" ".join(name).strip())])
                    break
                if type =='signature' or text in tname:
                    p_signature.append([self.summarize([sign_sort[i][0]])])
                    e_state=3
                    if text in tname:
                        name.insert(0,text)
                    continue
                if type=='personRole':
                    p_role.insert(0,sign_sort[i][0]) 
                    role.insert(0,spell(text.replace(",","").replace(".",""))[0])
            if i==0:
                p.insert(0,[self.summarize([sign_sort[end_current][0]])[1]])
        eximg_sign=self.extract_sign(self.delect_text(img_sign,p_signature),p)
        n=len(self.signature)
        #print(len(eximg_sign))
        for i in range(len(eximg_sign)):
            print('person: ',sign[i][1])
            person=PersonModel.tokenization_name(sign[i][1])
            print(' after token: ',person)
            if len(person) == 3:
                id=PersonModel.check_person(person[0],person[1],person[2])
                if not id:
                    print('not have')
                    id =PersonModel.current_person()+i+1+n
            else:
                id=PersonModel.current_person()+i+1+n
            self.signature.append({
                    "personId":id,
                    "personName":sign[i][1],
                    "personRole":sign[i][0],
                    "signatureImg":self.save_signature(self.keyword['documentId'],i,eximg_sign[i])
                    })
        return self.signature

    def save_signature(self,documentId,i,img_sign):
        cv2.imwrite('temp/sign_'+str(i)+'.png',img_sign)
        path_on_cloud = "document/{}/{}".format(documentId,'sign_'+str(i)+'.png')
        upload=storage.child(path_on_cloud).put('temp/sign_'+str(i)+'.png')
        url=storage.child(path_on_cloud).get_url(upload['downloadTokens'])
        return url
    
    def delect_text(self,img,position_text_around_sign):
        test=img.copy()
        print('position_text_around_sign: ',position_text_around_sign)
        for i in position_text_around_sign:
            for j in i:
                y1,y2,x1,x2,=j
                for k in range(y1,y2):
                    for l in range(x1,x2):test[k][l]=255 
        cv2.imwrite('test.png',test)
        return test

    def extract_sign(self,img_sign,add_sign):
        s=[]
        print(f"add :{add_sign}")
        for i in range(len(add_sign)-1): 
            print(isinstance(add_sign[i][0],int))
            if(isinstance(add_sign[i][0],int)):
                #sign=img_sign[add_sign[i][0][1]:add_sign[i+1][2][0],add_sign[i+1][0][3]:add_sign[i+1][1][2]].copy()
                sign=img_sign[add_sign[i][0]:add_sign[i+1][1][0],add_sign[i+1][1][2]:add_sign[i+1][1][3]].copy()
            else:
                #sign=img_sign[add_sign[i][2][1]:add_sign[i+1][2][0],add_sign[i+1][0][3]:add_sign[i+1][1][2]].copy()
                sign=img_sign[add_sign[i][1][1]:add_sign[i+1][1][0],add_sign[i+1][1][2]:add_sign[i+1][1][3]].copy()
                print(f"{add_sign[i][1][1]} {add_sign[i+1][1][0]} {add_sign[i+1][1][2]} {add_sign[i+1][1][3]}")
            cv2.imwrite(f's{i}.png',sign)
            # gray = cv2.cvtColor(sign,cv2.COLOR_BGR2GRAY)
            # image = img_as_float(gray)
            # image_binary = image < 0.5
            # out_skeletonize = morphology.skeletonize(image_binary)
            # temp=[]
            # w=len(sign)
            # h=len(sign[0])
            # for i in range(w):
            #     row=[]
            #     for j in range(h):
            #         if out_skeletonize[i][j]:
            #             row.append(255)
            #         else:row.append(0)
            #     temp.append(row)
            # data=np.array(temp,dtype=np.uint8)
            # thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # num_labels, labels_im = cv2.connectedComponents(thresh)
            # binaryImageClone = np.copy(labels_im)
            # common=Counter(chain.from_iterable(binaryImageClone))
            # #label=draw_label(binaryImageClone)
            
            # kernel = np.ones((2,2), np.uint8)
            # img_dilation = cv2.dilate(thresh, kernel, iterations=1)
            # lines = cv2.HoughLinesP(data, 1, np.pi/360, 20, minLineLength=200, maxLineGap=100)
            # #print('start',len(sign))
            # e=[]
            # l=[]
            # print('line: ',lines,' type:',type(lines))
            # if isinstance(lines,np.ndarray):
            #     for line in lines:
            #         row=[]
            #         for x1,y1,x2,y2 in line:
            #             #print(x1,y1,x2,y2)
            #             m = (y2 - y1) / (x2 - x1)
            #             c = y1 - m* x1
            #             row.append([m,c])
            #             for i in range(0,len(data[0])):
            #                 if(int(m*i+c) < len(gray) and m*i+c >=0):
            #                     if(labels_im[int(m*i+c)][i] != 0): l.append(labels_im[int(m*i+c)][i])
            #         e.append(row)
            #         label_del= list(set(l))
            #         kernel = np.ones((5,5), np.uint8)
            #         img_dilation = cv2.dilate(gray, kernel, iterations=1)
            #         for m in range(len(gray)):
            #             for n in range(len(gray[0])):
            #                 if( labels_im[m][n] in label_del and common[labels_im[m][n]] < w*h/1000 ):
            #                     gray[m][n]=255
            #         kernel = np.ones((3,3), np.uint8)
            #         img_dilation = cv2.dilate(gray, kernel, iterations=1) 
            #         img_erosion = cv2.erode(img_dilation, kernel, iterations=1)
            #     s.append(img_erosion)
            # else:
            s.append(sign)
            #print(s) 
        return s

    @jwt_required()
    def put(self):
        Extractparser = reqparse.RequestParser()
        Extractparser.add_argument('documentId',
                            type=int,
                            required=True,
                            help="This field cannot be blank.",
                            location='args'
                            )
        Extractparser.add_argument('type',
                            type=int,
                            required=True,
                            help="This field cannot be blank.",
                            location='args'
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
        self.keyword["documentId"]=Data['documentId']
        start_time = time.time()
        if Data['type'] == 0:
            with open('temp/page.json','w',encoding = 'utf-8') as r: 
                json.dump(Data['pages'],r,sort_keys=True,default=default,ensure_ascii=False)
        # orderPage=[]
        # h=0
        # for i in Data['pages']:
        #     for j,k in i.items():
        #         orderPage.append(int(j))
        #         DocumentModel.save_page(Data['documentId'],h,k)
        #         h+=1
            head=self.read_data(Data['type'],0)[0]
            print ("extract head time --- %s seconds ---" % (time.time() - start_time))
            # print('head: ')
            # for i in head:
            #    print (i)
            start_time=time.time()
            result=self.classify_head(head)
            print ("classify_head time --- %s seconds ---" % (time.time() - start_time))
            with open('temp/temp.json','w',encoding = 'utf-8') as r: 
                json.dump(result,r,sort_keys=True,default=default,ensure_ascii=False)
        elif Data['type'] == 1: 
            for i in Data['pages']:          
                for j,k in i.items():
                    signature,img_sign=self.read_data(Data['type'],j) 
                    print ("extract signature time --- %s seconds ---" % (time.time() - start_time))
                    print('signature:')
                    for i in signature:
                        print(i)
                    start_time=time.time()
                    result=self.classify_signature(signature,img_sign)
                    print ("classify_signature time --- %s seconds ---" % (time.time() - start_time))
        return make_response({
            'status': 'success',
            'data': result
        },200)
    @classmethod
    def read_page(cls):
        with open('temp/page.json', 'r',encoding="utf8") as openfile:
            json_object = json.load(openfile)
        return json_object

    def save_pre_to_db(self):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        sql = 'insert into document (documentId,p_title,p_sendAddress,p_receiver) value (%s,%s,%s,%s)'
        val=(self.keyword['documentId'],self.keyword['title'],self.keyword['sendAddress'],self.keyword['receiver'])
        mycursor.execute(sql,val)
        mydb.commit()
        mydb.close()
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
        saveparser.add_argument('dateWrite',
                            type= str,
                            required=True,
                            location='json',
                            help="This field cannot be blank."
                            )
        with open('temp/temp.json', 'r',encoding="utf8") as openfile:
            json_object = json.load(openfile)
        if not DocumentModel.find_doc_by_id(json_object['documentId']):
            for k in self.keyword:
                self.keyword[k]=json_object[k]
            self.save_pre_to_db()
        Data = saveparser.parse_args()
        doc=DocumentModel()
        for i in Data:
            value=Data[i]
            if i =='dateWrite':
                value=datetime.strptime(Data[i],"%a, %d %b %Y %H:%M:%S %Z").date()
            setattr(doc,i,value)
        check=doc.save_to_db()
        if(check==False):
            return {
                        'status':'failed',
                        'message':'Person invalid'},400
        pages=self.read_page()
        k=0
        for ps in pages:
            for m,n in ps.items():
                #print(f"pages key: {m} value: {n}")
                DocumentModel.save_page(doc.documentId,k,n)
            k+=1
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


