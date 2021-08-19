import mysql.connector,csv,os

tname=[]
with open('name.csv', newline=None,encoding='utf8') as f:
    reader = csv.reader(f)
    for row in reader:
        tname.append(row[0].strip())
#custom_tokenizer = Tokenizer(custom_dict=trie,engine='deepcut')
#print(custom_tokenizer.word_tokenize('นายวีระชัย สาระคุณ'))

class PersonModel:

    # def __init__(self,personId=None,person_tname=None,person_fname=None,person_lname=None):
    #     self.personId=personId
    #     self.person_tname=person_tname
    #     self.person_fname=person_fname
    #     self.person_lname=person_lname
    
    def save_person(self,fullname):
        #print('fullname: ',fullname)
        try:
            tname,fname,lname=self.tokenization_name(fullname)
        except ValueError as e:
            raise e("Person name not valid")
        #print(f'tname: {tname}  fname: {fname}  lname: {lname}')
        id_person =self.check_person(tname,fname,lname)
        print(id_person)
        if id_person :
            return id_person
        else: 
            print(id_person,tname,fname,lname)
            id_person=self.current_person()+1
            mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
            mycursor = mydb.cursor()
            sql = "INSERT INTO persons (id_person,person_tname,person_fname,person_lname) VALUES (%s,%s,%s,%s)"
            val = (id_person,tname,fname,lname)
            mycursor.execute(sql, val)
            mydb.commit()
            mydb.close()
            return id_person
    
    @classmethod
    def update_person(cls,id_person,fullname):
        #print('fullname:',cls.tokenization_name(fullname))
        tname,fname,lname=cls.tokenization_name(fullname)
        print(f'tname: {tname}  fname: {fname}  lname: {lname}')
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        query="Update persons set person_tname = %s ,person_fname = %s ,person_lname = %s where id_person = %s"
        mycursor.execute(query, (tname,fname,lname,id_person))
        mydb.commit()
        mydb.close()
    
    @classmethod
    def check_person(cls,tname,fname,lname):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        sql = "SELECT id_person FROM persons WHERE person_tname like '{}' and person_fname like '{}' and person_lname like '{}'".format(tname,fname,lname)
        mycursor.execute(sql)
        result = mycursor.fetchone()
        mydb.close()
        if result:
            #print('check_person',result)
            return result[0]
        else :
            return 0

    @classmethod
    def current_person(cls):
        mydb= mysql.connector.connect(host=os.getenv('host'),user=os.getenv('user'),passwd=os.getenv('password'),database=os.getenv('database'))
        mycursor = mydb.cursor()
        mycursor.execute("SELECT Max(id_person) FROM persons")
        result = mycursor.fetchone()
        mydb.close()
        if None not in result: 
            #print('current_person: ',result[0])
            return result[0]
        else: 
            return 0
    
    @classmethod
    def tokenization_name(cls,name):
        check=name.split('.')
        if len(check) > 1:
            l=name.rfind('.')+1
            name_not_point = name[l:].split()
            t=name[:l]
            result =[]
            for i in range(len(name_not_point)):
                if i> len(name_not_point)-3:
                    result.append(name_not_point[i])
                else:
                    t+=name_not_point[i]
            result.insert(0,t)
            return result
        else:
            temp = name.split()
            for i in tname:
                if temp[0] == i:
                    if len(temp)==3:
                        return temp
                    else:
                        return 0
                elif i in temp[0] and temp[0].index(i[0])==0:
                    result = name[:len(i)]+' '+name[len(i):]
                    #print('result:',result)
                    if len(result.split()) ==3:
                        return result.split()
            return 0