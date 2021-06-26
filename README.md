# document

# 1. install python

Download from https://www.python.org/

Window: 

        pip -V                                  // view version
        
        python -m pip install --upgrate pip     // update

Linux, Mac: 

        sudo apt install python3-pip    // download 
        
        sudo apt-get install pip        // update

# 2. create environment

Linux, Mac: 

        sudo pip install virtualenv

Window, Mac, Linux: 

        virtualenv venv

# 3. access environment

Window: 

        .\venv\scripts\activate

Linux, Mac: 

        source ./venv/bin/activate

# 4. install packget

        pip install Flask-RESTful

        pip install jwt

        pip install mysql-connector-python

# 5. run app

python api/app.py
