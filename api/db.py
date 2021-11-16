import mysql.connector,os

mydb= mysql.connector.connect(host="localhost",user="root",passwd="",database="doc",buffered=True)
print(mydb)