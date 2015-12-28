from flask import Flask, render_template, json, request, redirect, session, jsonify
from flask.ext.mysql import MySQL
from werkzeug import generate_password_hash, check_password_hash 

app = Flask(__name__)

mysql.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()

#Show the index.
@app.route("/")
def main():
    return render_template('index.html')

#Show the signup page.
@app.route('/showSignUp')
def showSignUp():
    return render_template("signup.html")

#Show the sign in page
@app.route('/showSignIn')
def showSignin():
    return render_template('signin.html')

#Direct the validated user home
@app.route('/userHome')
def userHome():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('error.html', error='You are not Authorized.')

#Validate login creds
@app.route('/validateLogin', methods=['POST'])
def validateLogin():
    try: 
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']   
    
        #connect to the db
        con = mysql.connect()
        cursor = con.cursor()
        cursor.callproc('sp_validateLogin', (_username,))
        data = cursor.fetchall()
        
        #check if data is correct, if so, allow the user in
        if len(data) > 0:
            if check_password_hash(str(data[0][3]), _password):
                session['user'] = data[0][0]
                return redirect('/userHome')
        else: 
            return render_template('error.html', error = 'Wrong email or password.')
        
    except Exception as e:
        return render_template('error.html', error = str(e))
        
#Handle Signup
@app.route('/signUp', methods=['POST'])
def signUp():
    #read the posted values from the UI
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']
    
    #hash the password
    _hashed_password = generate_password_hash(_password)
    cursor.callproc('sp_createUser', (_name, _email, _hashed_password))
    data = cursor.fetchall()
    #create the user
    if len(data) is 0:
        conn.commit()
        return json.dumps({'message': 'User created successfully !'})
    else:
        return json.dumps({'error': str(data[0])})

#Handle logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')
   
#Show the addwish page
@app.route('/showAddWish')
def showAddWish():
    return render_template('addWish.html')

#Post a new wish
@app.route('/addWish', methods=['POST'])
def addWish():
    #try to add the wish
    try: 
        #if the user session cookie exists
        if session.get('user'):
            _title = request.form['inputTitle']
            _description = request.form['inputDescription']
            _user = session.get('user')
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_addWish', (_title, _description, _user))
            data = cursor.fetchall()
            #if data present commit the request
            if len(data) is 0:
                conn.commit()
                return redirect('/userHome')
            else:
                return render_template('error.html', error='An error occured')
        else:
            #if the user cookie does not exist, user is not authorized
            return render_template('error.html', error='Unauthorized')
    #if wish cannot be added, throw an exception
    except Exception as e:
        return render_template('error.html', error= str(e))
    #close the connection
    finally:
        cursor.close()
        conn.close()

#Get the wishes to populate the list on userHome
@app.route('/getWish')
def getWish():
    try:
        if session.get('user'):
            _user = session.get('user')
            
            #fetch the user wishes
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetWishByUser', (_user,))
            wishes = cursor.fetchall()
            
            wishes_dict = []
            for wish in wishes:
                wish_dict = {
                    'Id': wish[0],
                    'Title': wish[1],
                    'Description': wish[2],
                    'Date': wish[4]
                }
                wishes_dict.append(wish_dict)
                #return json.dumps(wishes_dict)
            return jsonify(wishes=wishes_dict)
        else: 
            return render_template('error.html', error = 'Unauthorized')
    except Exception as e:
        return render_template('error.html', error=str(e))

    
#Grab a particular wish to allow for Updating
@app.route('/getWishById', methods=['POST'])
def getWishById():
    try: 
        if session.get('user'):
            _id = request.form['id']
            _user = session.get('user')
            
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetWishById', (_id, _user))
            result = cursor.fetchall()
            
            wish = []
            wish.append({
                    'Id':result[0][0],
                    'Title':result[0][1],
                    'Description':result[0][2]})
            return json.dumps(wish)
        else: 
            return render_template('error.html', error = 'Unauthorized')
    except Exception as e:
        return render_template('error.html', error = str(e))

#Update a gotten wish
@app.route('/updateWish', methods=['POST'])
def updateWish():
    try:
        if session.get('user'):
            _user = session.get('user')
            _title = request.form['title']
            _description = request.form['description']
            _wish_id = request.form['id']
            
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_updateWish', (_title, _description, _wish_id, _user))
            data = cursor.fetchall()
            
            if len(data) is 0:
                conn.commit()
                return json.dumps({'status': 'OK'})
            else:
                return json.dumps({'status': 'ERROR'})
        else:
            return render_template('error.html', error = 'Unauthorized')
    except Exception as e:
        return render_template('error.html', error = str(e))
    finally:
        cursor.close()
        conn.close()

#delete a wish
@app.route('/deleteWish', methods=['POST'])
def deleteWish():
    try:    
        if session.get('user'):
            _user = session.get('user')
            _wish_id = request.form['id']

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_deleteWish', (_wish_id, _user))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return json.dumps({'status':'OK'})
            else: 
                return json.dumps({'status': 'ERROR'})

        else:
            return render_template('error.html', error = 'Unauthorized')
    except Exception as e:
        return render_template('error.html', error = str(e))
    finally:
        cursor.close()
        conn.close()
        
        
if __name__ == "__main__":
    app.debug = True
    app.run()
    
