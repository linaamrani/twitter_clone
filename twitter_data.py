from sqlite3 import Connection as SQLite3Connection
from sqlalchemy import event
from sqlalchemy.engine import Engine
from flask import Flask, request, jsonify, flash, session, render_template, url_for, redirect, session, logging
from flask_sqlalchemy import SQLAlchemy
import linked_list
import hash_table
import hash_table1
from flask_wtf import FlaskForm
from passlib.hash import sha256_crypt
from wtforms.validators import InputRequired, Length, ValidationError
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SubmitField
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
import re


# app
app = Flask(__name__, template_folder='template', static_folder='static')

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlitedb.file"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = 0
app.secret_key = 'testing321'


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


db = SQLAlchemy(app)

# models
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def tweets_liked():
    likes = TweetLike.query.all()
    tweets_liked_by_user = {}
    for like in likes:
        if tweets_liked_by_user.get(like.user_id) is not None:
            if like.tweet_id not in tweets_liked_by_user.get(like.user_id):
                tweets_liked_by_user.get(like.user_id).append(like.tweet_id)
        else:
            tweets_liked_by_user[like.user_id] = [like.tweet_id]
    return tweets_liked_by_user

#IMPLEMENTATION OF ALL CLASSES#


class Friendship(db.Model):
    __tablename__ = "friendship"
    uid1 = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    uid2 = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True,
                   nullable=False)
    username = db.Column(db.String(24), unique=True)
    email = db.Column(db.String(64), unique=True)
    pwd = db.Column(db.String(64))
    tweets = db.relationship(
        "Tweet", cascade="all, delete", backref='tweeter', lazy=True)
    friendships = db.relationship(
        "Friendship", cascade="all, delete", backref='friends', foreign_keys=[Friendship.uid1])
    friendships_ = db.relationship(
        "Friendship", cascade="all, delete", backref='friend', foreign_keys=[Friendship.uid2])
    liked = db.relationship(
        'TweetLike',
        foreign_keys='TweetLike.user_id',
        backref='user', lazy='dynamic')
    tweetlike = db.relationship(
        "TweetLike", cascade="all, delete", backref='liker', lazy=True, overlaps="liked,user")

    def like_tweet(self, tweet):
        if not self.has_liked_tweet(tweet):
            like = TweetLike(user_id=self.id, tweet_id=tweet.id)
            db.session.add(like)

    def unlike_tweet(self, tweet):
        if self.has_liked_tweet(tweet):
            TweetLike.query.filter_by(
                user_id=self.id,
                tweet_id=tweet.id).delete()

    def has_liked_tweet(self, tweet):
        likes = tweets_liked().get(self.id)
        if likes is not None:
            for tid in likes:
                if tid == tweet.id:
                    return True
        return False


class TweetLike(db.Model):
    __tablename__ = 'tweet_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'))


class Tweet(db.Model):
    __tablename__ = "tweet"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(256))
    content = db.Column(db.String(2048))
    likes = db.relationship("TweetLike", backref='tweet', lazy='dynamic')


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "username"})
    email = StringField(validators=[InputRequired(), Length(
        min=10, max=30)], render_kw={"placeholder": "email"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "password"})
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Length(
        min=10, max=30)], render_kw={"placeholder": "email"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "password"})
    submit = SubmitField("Login")


class PostForm(Form):
    tweet = TextAreaField('', [validators.Length(min=1, max=2048)])
    title = TextAreaField('', [validators.Length(min=1, max=2048)])


class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[InputRequired()])
    submit = SubmitField("Submit")


def current_user():
    if len(session) > 0:
        return User.query.filter_by(id=session['_user_id']).first()
    else:
        return None


def get_user_by_email(email):
    # first we need to load all the data from the databse and store it in memory
    # fast data retrieval
    users = User.query.all()
    # we create a hash table to store the users (usernames are unique, they are the keys)
    users_hash = hash_table1.HashTable()
    for u in users:
        users_hash.put(
            u.email, u)
    return users_hash.get(email)


@app.route("/", methods=['GET', 'POST'])
def log():
    form = LoginForm()
    if request.method == 'POST':
        # get fields from form
        email = request.form.get('email')
        password_input = request.form.get('password')
        user = get_user_by_email(email)
        # If there is a user with the email
        if user != None:
            password = user.pwd
            # If passwords match
            if sha256_crypt.verify(password_input, password):
                flash('You are now logged in', 'success')
                login_user(user, remember=True)
                return redirect(url_for('home'))
            # If passwords don't match
            else:
                error = 'Invalid password'
                return render_template('login.html', error=error, form=form)
        # No user with the email
        else:
            error = 'Email not found'
            return render_template('login.html', error=error, form=form)
    return render_template('login.html', form=form)


@ app.route("/template/register.html", methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        # get input data
        email = request.form.get('email')
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        # create user
        user = User(username=username, email=email, pwd=password)
        # Add user to database
        db.session.add(user)
        db.session.commit()
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))
    print('here')
    return render_template('register.html', form=form)


@app.route("/template/login.html", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        email = request.form.get('email')
        password_input = request.form.get('password')
        user = get_user_by_email(email)
        if user != None:
            password = user.pwd
            if sha256_crypt.verify(password_input, password):
                flash('You are now logged in', 'success')
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                error = 'Invalid password'
                return render_template('login.html', form=form, error=error)
        else:
            error = 'Email not found'
            return render_template('login.html', form=form, error=error)
    return render_template('login.html', form=form)


def get_follows():
    # creates a dictionnary with a user as a key and the the list of users followed by him as value
    friendships = Friendship.query.all()
    follows = {}
    for f in friendships:
        if follows.get(f.uid1) is not None:
            if f.uid2 not in follows.get(f.uid1):
                follows.get(f.uid1).append(f.uid2)
        else:
            follows[f.uid1] = [f.uid2]
    return follows


def following(uid):
    # get the list of followings for a specific user id
    friends = get_follows().get(uid)
    return friends


def is_followed_by(uid1, uid2):
    # return true if uid1 is followed by uid2
    followings = following(uid2)
    if followings is not None:
        if uid1 in followings and uid1 != uid2:
            return True
    return False


def follow_relationship():
    # list of tuples (i,j) such that i follows j
    follow_relationship = []
    for friend in Friendship.query.all():
        follow_relationship.append((friend.uid1, friend.uid2))
    return follow_relationship


def follow_relation_dic():
    # dictionnary dico:{id1 : {id2: True, id3:True ,...}, id2: {id5: True,...}, ...}
    # dictionnary of dictionnaries to represent follow relationship
    follow_relation_dic = {}
    follow_ = follow_relationship()
    for f in follow_:
        if follow_relation_dic.get(f[0]) is not None:
            if follow_relation_dic.get(f[0]).get(f[1]) is not None:
                continue
            else:
                follow_relation_dic.get(
                    f[0])[f[1]] = True
        else:
            follow_relation_dic[f[0]] = {f[1]: True}
    return follow_relation_dic


def is_symmetric():
    # question 1.a
    # complexity in O(n) for n number of keys in dico
    # get in o(1) so get.get in O(1)
    # returns a list of tuples [(i,j)] such that i follows j and j follows i
    dico = follow_relation_dic()
    sym = []
    for (i, j) in follow_relationship():
        if (i < j and dico.get(i) is not None
            and dico.get(j) is not None
                and dico.get(i).get(j) == dico.get(j).get(i)):
            sym.append((i, j))
    return sym


def name_to_id_mapping():
    # mapping for question 1.b
    users = User.query.all()
    users_by_username = {}
    for u in users:
        if users_by_username.get(u.username) is not None:
            if u not in users_by_username.get(u.username):
                users_by_username.get(u.username).append(u.id)
        else:
            users_by_username[u.username] = u.id
    return users_by_username


def names_sym():
    # answer for question 1.b
    name_to_id = name_to_id_mapping()
    sym = is_symmetric()
    li = set()
    for (i, j) in sym:
        li.add(i)
        li.add(j)
    names = []
    for n in name_to_id.keys():
        if name_to_id.get(n) in list(li):
            names.append(n)
    return names

# To display the names of users that are involved in a symetric relationship
# uncomment the following code line
# print(names_sym())


def tweets_by_user():
    tweets = Tweet.query.all()
    tweets_by_user = {}
    for tweet in tweets:
        if tweets_by_user.get(tweet.uid) is not None:
            if tweet not in tweets_by_user.get(tweet.uid):
                tweets_by_user.get(tweet.uid).append(tweet)
        else:
            tweets_by_user[tweet.uid] = [tweet]
    return tweets_by_user


def get_users_followed():
    # gets both users followed and users not followed
    follows = following(current_user().id)
    all_users = User.query.all()
    users_not_followed = []
    users_followed = []
    for user in all_users:
        if follows is not None:
            if ((user.id not in follows) and (user.id != current_user().id)):
                users_not_followed.append(user)
            elif ((user.id in follows) and (user.id != current_user().id)):
                users_followed.append(user)
        else:
            if user.id != current_user().id:
                users_not_followed.append(user)
    return users_followed, users_not_followed


@app.route("/template/home.html", methods=['GET', 'POST', 'DELETE'])
def home():
    form = PostForm()
    if request.method == 'POST':
        tweet = request.form.get('Tweet')
        title = request.form.get('Title')
        print("nouveau tweet")
        print(tweet)
        print(title)
        # create tweet
        new_tweet = Tweet(uid=current_user().id, content=tweet, title=title)
        # add tweet to database
        db.session.add(new_tweet)
        db.session.commit()
        flash('New tweet posted!', 'success')
        return redirect(url_for('home'))
    if current_user():
        tweets = []
        follows = following(current_user().id)
        all_users = User.query.all()
        if follows is not None:
            for follow in follows:  # Get all the tweets for followed accounts
                user_tweets = tweets_by_user().get(follow)
                if user_tweets is not None:
                    tweets += user_tweets
        perso_tweets = tweets_by_user().get(current_user().id)
        if perso_tweets is not None:
            tweets += perso_tweets  # add personal tweets
            tweets.reverse()
        # get all users not followed for the following suggestions and users followed
        users_followed, users_not_followed = get_users_followed()
        return render_template('home.html', tweets=tweets, users_followed=users_followed, all_users=all_users, form=form, user=current_user(), users_not_followed=users_not_followed)
    else:
        return render_template('login.html')


def words_in_all_tweets():
    tweets = Tweet.query.all()
    words_dico = {}
    for tweet in tweets:
        title = tweet.title.lower().split(" ")
        content = tweet.content.lower().split(" ")
        # for every word, we put it as a key in a hashtable with as values the tweets it appears in
        for word in title:
            if words_dico.get(word) is not None:
                if tweet.id not in words_dico.get(word):
                    words_dico.get(word).append(tweet.id)
            else:
                words_dico[word] = [tweet.id]
        for word in content:
            if words_dico.get(word) is not None:
                if tweet.id not in words_dico.get(word):
                    words_dico.get(word).append(tweet.id)
            else:
                words_dico[word] = [tweet.id]
    return words_dico


def get_tweets():
    # put all tweets in a dictionary with the tweet_id as the key and informations in a list as value
    # used for fast retrieval of the tweets data
    tweets_dico = {}
    tweets = Tweet.query.all()
    for tweet in tweets:
        tweets_dico[tweet.id] = [tweet.uid,
                                 tweet.title, tweet.content, tweet.likes, tweet]
    return tweets_dico


@app.route("/search", methods=["POST", "GET", "DELETE"])
def search():
    form = SearchForm(request.form)
    words_dico = words_in_all_tweets()
    all_users = User.query.all()
    word_searched = request.form.get('searched').lower()
    if word_searched is None:
        word_searched = ''
    tweets = get_tweets()
    id_tweets_with_word = words_dico.get(word_searched)
    if id_tweets_with_word is None:
        id_tweets_with_word = []
    users_followed, users_not_followed = get_users_followed()
    return render_template("search.html", form=form, all_users=all_users, word_searched=word_searched, tweets=tweets, ids=id_tweets_with_word, current_user=current_user(), users_not_followed=users_not_followed)


@app.route("/myprofile", methods=["POST", "GET", "DELETE"])
def myprofile():
    users_followed, users_not_followed = get_users_followed()
    users_following_me = []
    all_users = User.query.all()
    for user in all_users:
        if (is_followed_by(current_user().id, user.id)):
            users_following_me.append(user)
    perso_tweets = tweets_by_user().get(current_user().id)
    if perso_tweets is None:
        perso_tweets = []
    return render_template("myprofile.html", current_user=current_user(), users_followed=users_followed, users_not_followed=users_not_followed, users_following_me=users_following_me, perso_tweets=perso_tweets)


@app.route("/profile/<int:user_id>", methods=["POST", "GET", "DELETE"])
def profile(user_id):
    user_ = user_by_id().get(user_id)[0]
    users_followed, users_not_followed = get_users_followed()
    users_following_uid = []
    all_users = User.query.all()
    for user in all_users:
        if (is_followed_by(user_.id, user.id)):
            users_following_uid.append(user)
    user_tweets = tweets_by_user().get(user_.id)
    if user_tweets is None:
        user_tweets = []
    return render_template("profile.html", user=user_, current_user=current_user(), users_followed=users_followed, users_not_followed=users_not_followed, users_following_uid=users_following_uid, user_tweets=user_tweets)


@app.route("/delete/<int:id>")
def delete(id):
    # for deleting a tweet
    tweet_to_delete = Tweet.query.get_or_404(id)
    db.session.delete(tweet_to_delete)
    db.session.commit()
    return redirect(request.referrer)


@app.route("/delete_account/<int:user_id>")
def delete_account(user_id):
    user_to_delete = user_by_id().get(user_id)[0]
    db.session.delete(user_to_delete)
    db.session.commit()
    flash('Account deleted')
    return redirect(url_for('login'))


@app.route("/follow/<int:id>")
def follow(id):
    id_to_follow = id
    current_id = current_user().id
    new_follow = Friendship(uid1=current_id, uid2=id_to_follow)
    db.session.add(new_follow)
    db.session.commit()
    if 'search' in request.referrer:
        return redirect(url_for('home'))
    return redirect(request.referrer)


@app.route("/unfollow/<int:id>")
def unfollow(id):
    id_to_unfollow = id
    current_id = current_user().id
    to_delete = Friendship.query.filter_by(
        uid1=current_id, uid2=id_to_unfollow).first()
    db.session.delete(to_delete)
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/like/<int:tweet_id>/<action>")
def like(tweet_id, action):
    tweet = get_tweets().get(tweet_id)[4]
    if action == 'like':
        current_user().like_tweet(tweet)
        db.session.commit()
    if action == 'unlike':
        current_user().unlike_tweet(tweet)
        db.session.commit()
    route = request.url_rule
    return redirect(request.referrer)


def follower_relationship():
    # return a list of tuples [(i,j)] such that  is a follower of j
    # j is following i
    follower_relationship = []
    for friend in Friendship.query.all():
        follower_relationship.append((friend.uid2, friend.uid1))
    return follower_relationship


def get_followers():
    # returns a dictionary with as a key a user id and as a value a set of user id that follow him
    friendships = Friendship.query.all()
    followers = {}
    for f in friendships:
        if followers.get(f.uid2) is not None:
            if f.uid1 not in followers.get(f.uid2):
                followers.get(f.uid2).add(f.uid1)
        else:
            followers[f.uid2] = {f.uid1}
    return followers


def follow_relationship2():
    # returns a dictionary with as a key a user id and as a value a dictionary of user id
    # that follow him as a key and a set of user that follow the user following
    follow_relation2_dic = {}
    follower_ = follower_relationship()
    for f in follower_:
        if follow_relation2_dic.get(f[0]) is not None:
            if follow_relation2_dic.get(f[0]).get(f[1]) is not None:
                continue
            else:
                follow_relation2_dic.get(
                    f[0])[f[1]] = get_followers().get(f[1])
        else:
            follow_relation2_dic[f[0]] = {f[1]: get_followers().get(f[1])}
    return follow_relation2_dic


def followers_of_followers(uid):
    # answer to question2
    follow2 = follow_relationship2()
    followers_of_followers = set()
    followers = follow2.get(uid)
    for k in followers.keys():
        followers_of_followers = followers_of_followers.union(followers.get(k))
    return followers_of_followers


def user_by_id():
    users = User.query.all()
    users_by_id = {}
    for u in users:
        if users_by_id.get(u.id) is not None:
            if u not in users_by_id.get(u.id):
                users_by_id.get(u.id).append(u)
        else:
            users_by_id[u.id] = [u]
    return users_by_id


def user_by_username():
    users = User.query.all()
    users_by_username = {}
    for u in users:
        if users_by_username.get(u.username) is not None:
            if u not in users_by_username.get(u.username):
                users_by_username.get(u.username).append(u)
        else:
            users_by_username[u.username] = [u]
    return users_by_username


def get_email_by_username(username):
    # midterm question 1
    # first we need to load all the data from the databse and store it in memory
    # fast data retrieval
    users = User.query.all()
    # we create a hash table to store the users (usernames are unique, they are the keys)
    users_hash = hash_table1.HashTable()
    for u in users:
        users_hash.put(
            u.username, {'id': u.id, 'username': u.username, 'email': u.email})
    return users_hash.get(username)['email']


def store_followings():
    follows = Friendship.query.all()
    followings_hash = hash_table.HashTable(len(follows))
    for f in follows:
        followings_hash.put(f.uid1, f.uid2)
    return followings_hash


def is_following(user_following, user_followed):
    # putting in a linked list all the users followed by user_following
    followings = store_followings().get(user_following)
    if followings is not None and followings.size > 1:
        followings = followings.to_list()
    elif followings is not None:
        if followings == user_followed:
            return True
        return False
    for f in followings:
        if f == user_followed:
            return True
    return False

# other implementation of is_following with hashtable


def is_following_hash(user_following, user_followed):
    # putting in a linked list all the users followed by user_following
    followings = store_followings().get(user_following).to_list()
    # build a hash table for the followings of this specific user
    followings_hash = hash_table.HashTable(len(followings))
    for i in (followings):
        followings_hash.put(i, 'True')
    if followings_hash.get(user_followed) is not None:
        return True
    return False


@ app.route("/api/users", methods=["GET", "POST", "DELETE"])
def users():
    if request.method == 'POST':
        data = request.get_json()
        new_user = User(username=data["username"],
                        email=data["email"], pwd=data["pwd"])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created"}), 200

    if request.method == 'DELETE':
        username = request.get_json()["username"]
        # user = User.query.filter_by(id=user_id)
        user = user_by_username().get(username)
        if not user:
            return jsonify({"message": "User not found"})
        db.session.delete(user[0])
        db.session.commit()
        return jsonify({"message": "User deleted"}), 200

    else:  # GET
        user_id = request.get_json()
        users = User.query.all()
        users_list = linked_list.LinkedList()
        for u in users:
            users_list.insert_beginning(
                {"id": u.id, "username": u.username,
                 "email": u.email, 'pwd': u.pwd}
            )

        user = users_list.get_user_by_id((user_id))
        if user is None:
            return jsonify({"message": "user not found"}), 400
        return jsonify(user)


'''
    if request.method == 'DELETE':
        user_id = request.get_json()["id"]
        # user = User.query.filter_by(id=user_id)
        user = user_by_id().get(user_id)
        if not user:
            return jsonify({"message": "User not found"})
        db.session.delete(user[0])
        db.session.commit()
        return jsonify({"message": "User deleted"}), 200
'''


@ app.route("/api/tweets", methods=["GET", "POST", "DELETE"])
def tweets():

    if request.method == 'GET':
        user_id = request.get_json()["uid"]
        # tweets = Tweet.query.filter_by(uid=user_id)
        tweets = tweets_by_user(user_id)
        tweet_list = linked_list.LinkedList()
        for t in tweets:
            tweet_list.insert_at_end(
                {"id": t.id, "uid": t.uid, "title": t.title, "content": t.content})
        if len(tweet_list.to_list()) == 0:
            return jsonify({"message": "Tweets not found"})
        return jsonify(tweet_list.to_list()), 200

    if request.method == 'POST':
        data = request.get_json()
        new_user = Tweet(
            uid=data["uid"], title=data["title"], content=data["content"])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Tweet created"}), 200

    if request.method == 'DELETE':
        tweet_id = request.get_json()["id"]
        tweet = Tweet.query.filter_by(id=tweet_id)
        if not tweet:
            return jsonify({"message": "Tweet not found"})
        db.session.delete(tweet[0])
        db.session.commit()
        return jsonify({"message": "Tweet deleted"}), 200


@app.route("/api/friendships", methods=['GET', "POST", "DELETE"])
def friendships():
    if request.method == 'DELETE':
        # deleting all relationship involving uid1 whether he is following or followed
        uid1 = request.get_json()["uid1"]
        uid2 = request.get_json()["uid2"]
        f = Friendship.query.filter_by(uid1=uid1, uid2=uid2).first()
        #followed = Friendship.query.filter_by(uid2=uid1)
        # for f in friends:
        db.session.delete(f)
        db.session.commit()
        # for f in followed:
        # db.session.delete(f)
        # db.session.commit()
        return jsonify({"message": "Friendships deleted"}), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="localhost", port=int("5000"))
