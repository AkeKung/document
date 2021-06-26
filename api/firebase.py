import pyrebase
from dotenv import dotenv_values

config = dotenv_values(".env")
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
#Upload
# path_on_cloud = "document/1.pdf"
# path_local = "ใบรายงานตัวเข้ารับการฝึกงาน.jpeg"
# upload=storage.child(path_on_cloud).put(path_local)

#download
#storage.child(path_on_cloud).download("test_1.pdf")

#get url
#auth = firebase.auth()
#email = "weerachai"
# url=storage.child(path_on_cloud).get_url(upload['downloadTokens'])
# print(url)