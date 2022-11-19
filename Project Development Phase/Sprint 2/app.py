from flask import Flask, redirect, url_for, request, render_template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import urllib.parse
import ibm_db

app = Flask(__name__)


conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=9938aec0-8105-433e-8bf9-0fbb7e483086.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32459;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=znq27181;PWD=********","","")

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/aboutus')
def aboutus():
	return render_template('aboutus.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/statistics1')
def statistics1():
    return render_template('statistics1.html')

@app.route('/requested', methods=['GET','POST'])
def requested():
	clean_data = ''
	if request.method == 'POST':
		content = request.get_data()
		# Parse query string part of a URL, and return a dictionary of the data
		x = urllib.parse.parse_qs(content)
		# clean noise that is, remove prefix character 'b
		for k, v in x.items():
			for i in v:
				clean_data = clean_data + i.decode('utf-8')+"\n"
		clean_data = clean_data.split("\n")
		# Enumerate user data
		blood = clean_data[0]
		address = clean_data[1]
		msg = "Need Plasma of your blood group for: "+address
		sql = "SELECT EMAIL FROM user WHERE blood='"+blood+"'"
		stmt = ibm_db.exec_immediate(conn, sql)
		dictionary = ibm_db.fetch_both(stmt)
		while dictionary != False:
			print(dictionary[0])
			mail_msg = Mail(from_email='abcd@gmail.com',to_emails=''+dictionary[0],
						subject='Need Plasma',html_content='<strong>'+msg+'</strong>')
			sg = SendGridAPIClient("apikey")
			mail_response = sg.send(mail_msg)
			print(mail_response)
			dictionary = ibm_db.fetch_both(stmt)
		messages = {'message': 'Your request is sent to the concerned people.'}
		return render_template('request.html', messages=messages)
	return render_template('request.html')

@app.route('/signin',  methods=['GET', 'POST'])
def signin():
	clean_data = ''
	if request.method == 'POST':
		content = request.get_data()
		x = urllib.parse.parse_qs(content)
		for k, v in x.items():
			for i in v:
				clean_data = clean_data + i.decode('utf-8')+"\n"
		clean_data = clean_data.split("\n")
		email = clean_data[0]
		passw = clean_data[1]
		sql = "SELECT * FROM user WHERE email =? AND password=?"
		stmt = ibm_db.prepare(conn, sql)
		ibm_db.bind_param(stmt,1,email)
		ibm_db.bind_param(stmt,2,passw)
		ibm_db.execute(stmt)
		account = ibm_db.fetch_assoc(stmt)
		if account:
			return redirect(url_for('statistics'))
		else:
			messages = {'message': 'Login unsuccessful. Incorrect username / password !'}
			return render_template('login.html', messages=messages)
	return render_template('login.html')

@app.route('/statistics')
def statistics():
	sql = "SELECT blood, count(blood) FROM user group by blood"
	stmt = ibm_db.exec_immediate(conn, sql)
	dictionary = ibm_db.fetch_both(stmt)
	data = []
	while dictionary != False:
		case = {'group': dictionary[0], 'count': dictionary[1]}
		data.append(case)
		dictionary = ibm_db.fetch_both(stmt)
	return render_template('statistics.html', data=data)

@app.route('/register', methods=['GET', 'POST'])
def register():
	clean_data = ''
	if request.method == 'POST':
		content = request.get_data()
		x = urllib.parse.parse_qs(content)
		for k, v in x.items():
			for i in v:
				clean_data = clean_data + i.decode('utf-8')+"\n"
		clean_data = clean_data.split("\n")
		# Enumerate user data
		username = clean_data[0]
		email = clean_data[1]
		phone = clean_data[2]
		city = clean_data[3]
		infect = clean_data[4]
		blood = clean_data[5]
		password = clean_data[6]
		query = "SELECT * FROM user WHERE email ='"+email+"'"
		stmt = ibm_db.exec_immediate(conn, query)
		row = ibm_db.fetch_assoc(stmt)
		if row:
			messages = {'message':'User already exist. Please login with details'}
			return render_template('register.html', messages=messages)
		else:
			insert_sql = "INSERT INTO  user VALUES (?, ?, ?, ?, ?, ?, ?)"
			prep_stmt = ibm_db.prepare(conn, insert_sql)
			ibm_db.bind_param(prep_stmt, 1, username)
			ibm_db.bind_param(prep_stmt, 2, email)
			ibm_db.bind_param(prep_stmt, 3, phone)
			ibm_db.bind_param(prep_stmt, 4, city)
			ibm_db.bind_param(prep_stmt, 5, infect)
			ibm_db.bind_param(prep_stmt, 6, blood)
			ibm_db.bind_param(prep_stmt, 7, password)
			ibm_db.execute(prep_stmt)
			messages = {'message': 'Registration success. Please login'}
			return render_template('register.html', messages=messages)
	else:
		return render_template('register.html')

if __name__ == '__main__':
	app.run(debug=True)
