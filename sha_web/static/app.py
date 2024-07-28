from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_mail import Mail, Message
import random, string


app = Flask(__name__)
app.secret_key = 'your_secret_key'

#client = MongoClient("mongodb://localhost:27017/")
#db = client["sha"]

#메일 보내기
mail = Mail(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'babg6748@gmail.com'
app.config['MAIL_PASSWORD'] = 'ezfl vvni nhka qkvf'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


app.config["MONGO_URI"] = "mongodb://localhost:27017/sha"
mongo = PyMongo(app)

# 임시 데이터 
# users = {}
# posts = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email_code = request.form.get('email-code')
        if email_code != session.get('email_code'):
            return "인증 코드가 올바르지 않습니다.", 400
    if request.method == 'POST':
        username = request.form['username'] # username은 user_Id로 바꿀 것.
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        full_name = request.form['full_name']
        email = request.form['email']
        # user_name 추가! 
    
        # if 'username_checked' not in session or not session['username_checked']:
        #    return "<script>alert('ID 중복 체크!'); window.history.back();</script>"

        if password == confirm_password:
            existing_user = mongo.db.users.find_one({'username' : username})
            if existing_user:
                return "ID가 이미 존재합니다."
            else:
                mongo.db.users.insert_one({
                    'username': username,
                    'password': password,
                    'full_name': full_name,
                    'email': email
                })
                session['username'] = username
                session['full_name'] = full_name
                return redirect(url_for('index'))
        else:
            return "비밀번호가 일치하지 않습니다."
    
    return render_template('signup.html')

@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.form['username']
    existing_user = mongo.db.users.find_one({'username' : username})
    if existing_user:
        return jsonify({'exists': True})
    else:
        session['username_checked'] = True
        return jsonify({'exists': False})
    
def generate_random_code(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.route('/submit_email', methods=['POST'])
def submit_email():
    email = request.form.get('email')
    code = generate_random_code()
    session['email_code'] = code

    try:
        msg = Message('SHA 게시판 인증메일', sender='babg6748@gmail.com', recipients=[email])
        msg.body = (
            f'SHA 게시판 인증메일\n'
            f'귀하의 인증번호는 {code}입니다.\n'
            '이메일을 인증하려면 위의 인증번호를 입력하세요.'
        )

        mail.send(msg)
        return jsonify({'success': True, 'code': code})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = mongo.db.users.find_one({'username' : username})
        if user and user['password'] == password:
            session['username'] = username
            session['full_name'] = user['full_name']
            return redirect(url_for('dashboard'))
        else:
            return "로그인 정보가 일치하지 않습니다."
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        # 게시글을 최신순으로 정렬
        posts = mongo.db.posts.find().sort('date_posted', -1)
        username = session['username']
        return render_template('dashboard.html', posts=posts, username=username)
    else:
        return redirect(url_for('login'))



@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('full_name', None)
    return redirect(url_for('index'))

@app.route('/write', methods=['GET', 'POST'])
def write():
    if 'username' in session:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            author = session['username']

            # 새 게시글 문서 생성
            new_post = {
                'title': title,
                'content': content,
                'author': author,
                'date_posted': datetime.now()
            }
            mongo.db.posts.insert_one(new_post)

            # 게시글 번호 재정렬
            reorganize_post_numbers()

            # 게시글 번호 업데이트
            last_post = mongo.db.posts.find_one(sort=[("post_number", -1)])
            if last_post:
                next_post_number = last_post['post_number'] + 1
            else:
                next_post_number = 1

            mongo.db.settings.update_one(
                {'_id': 'last_post_number'},
                {'$set': {'number': next_post_number}},
                upsert=True
            )

            return redirect(url_for('dashboard'))
        return render_template('write.html')
    else:
        return redirect(url_for('login'))


    
@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    
    
    if 'username' in session:
        post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
        if post:
            if request.method == 'POST':
                title = request.form['title']
                content = request.form['content']
                mongo.db.posts.update_one(
                    {'_id': ObjectId(post_id)},
                    {'$set': {'title': title, 'content': content}}
                )
                return redirect(url_for('post', post_id= post_id))
            return render_template('edit_post.html', post=post)
        else:
            if not post:
                return "게시글을 찾을 수 없습니다."
            if post['_id'] != session['username']: # _id? post_id?
                return "권한이 없습니다."
    else:
        return redirect(url_for('login'))

@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    if 'username' in session:
        post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
        if post:
            mongo.db.posts.delete_one({'_id': ObjectId(post_id)})
            reorganize_post_numbers()  # 번호 재정렬 함수 호출
            return redirect(url_for('dashboard'))
        else:
            return "게시글을 찾을 수 없습니다."
    else:
        return redirect(url_for('login'))

def reorganize_post_numbers():
    posts = mongo.db.posts.find().sort('date_posted', 1)  # 날짜 순서대로 정렬
    new_number = 1
    for post in posts:
        mongo.db.posts.update_one(
            {'_id': post['_id']},
            {'$set': {'post_number': new_number}}
        )
        new_number += 1

@app.route('/post/<post_id>', methods=['GET', 'POST'])
def post(post_id):
    if 'username' in session:
        post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
        if post:
            comments = list(mongo.db.comments.find({'post_id':ObjectId(post_id)}).sort('date_posted', 1))
            return render_template('post.html', post=post, comments=comments)
        else:
            return "게시글을 찾을 수 없습니다."
    else:
        return redirect(url_for('login'))

@app.route('/submit_comment/<post_id>', methods=['POST'])
def submit_comment(post_id):
    if 'username' in session:
        content = request.form['comment']
        author = session['username']
        new_comment = {
            'post_id': ObjectId(post_id),
            'content': content,
            'author': author,
            'date_posted': datetime.now()
        }
        mongo.db.comments.insert_one(new_comment)
        return redirect(url_for('post', post_id=post_id))
    else:
        return redirect(url_for('login'))

@app.route('/edit_comment/<comment_id>', methods=['GET', 'POST'])
def edit_comment(comment_id):
    if 'username' in session:
        comment = mongo.db.comments.find_one({'_id': ObjectId(comment_id)})
        if comment:
            if request.method == 'POST':
                content = request.form['content']
                mongo.db.comments.update_one(
                    {'_id': ObjectId(comment_id)},
                    {'$set': {'content': content}}
                )
                return redirect(url_for('post', post_id=comment['post_id']))
            return render_template('edit_comment.html', comment=comment)
        else:
            return "댓글을 찾을 수 없습니다."
    else:
        return redirect(url_for('login'))

@app.route('/delete_comment/<comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if 'username' in session:
        comment = mongo.db.comments.find_one({'_id': ObjectId(comment_id)})
        if comment:
            mongo.db.comments.delete_one({'_id': ObjectId(comment_id)})
            return redirect(url_for('post', post_id=comment['post_id']))
        else:
            return "댓글을 찾을 수 없습니다."
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
