import os
import secrets
from sqlalchemy import or_
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, session, Blueprint ,jsonify
from flask import current_app
from musicapp import db, bcrypt
from musicapp.forms import (MultiCheckboxField, RegistrationForm, LoginForm, UpdateAccountForm, GenreFilterForm, 
                            RequestResetForm, ResetPasswordForm, AddMusicForm, CommentForm)
from musicapp.models import User, Playlist, Music, Comment, Membership, PurchasedMembership, Genre, PlaylistMusic, MusicMetrics
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime

# Create a Blueprint for routes
bp = Blueprint('main', __name__)

# Home Page
@bp.route("/")
@bp.route("/home")
def home():
    return render_template('home.html')

# User Registration
@bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user_role = "creator" if form.creator_submit.data else "user"
        user = User(username=form.username.data, password=hashed_password, role=user_role)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

# User Login
@bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.tryna_user.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

# User Logout
@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

# Save Uploaded Profile Image
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (300, 300)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_fn
    
# Save Uploaded Music Cover Image
def save_cover(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/cover_pics', picture_fn)

    output_size = (300, 300)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_fn

# User Account Page
@bp.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.bank_details = form.bank_details.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@bp.route("/adding_music", methods=['GET', 'POST'])
@login_required
def new_music():
    form = AddMusicForm()
    if form.validate_on_submit():
        if 'music_file' not in request.files or request.files['music_file'].filename == '':
            flash("You must upload a music file!", "danger")
            return render_template('addmusic.html', title='Adding Music', form=form)

        file = request.files['music_file']
        
        # Get the next possible ID manually
        latest_music = Music.query.order_by(Music.id.desc()).first()
        next_id = (latest_music.id + 1) if latest_music else 1

        # Save file with new ID as filename
        filename = f"{next_id}.mp3"
        filename = secure_filename(filename)
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        
        if form.cover_picture.data:
            picture_file = save_cover(form.cover_picture.data)
            music = Music(
                title=form.title.data, creator_id=current_user.id, upload_date = datetime.utcnow(), cover_image_file=picture_file, genre_id=form.genre.data, shareable = form.shareable.data, premium = form.premium.data  
            )
        else:
            music = Music(
                title=form.title.data, creator_id=current_user.id, upload_date = datetime.utcnow(), genre_id=form.genre.data, shareable = form.shareable.data, premium = form.premium.data
            )

        db.session.add(music)
        db.session.commit()
        
        music_metrics = MusicMetrics(music_id=music.id)
        db.session.add(music_metrics)
        db.session.commit()
        flash(f'Music "{form.title.data}" has been added!', 'success')
        return redirect(url_for('main.music_library'))
    
    return render_template('addmusic.html', title='Adding Music', form=form)

# View Music Library
@bp.route("/music_library")
def music_library():
    genres = [genre.name for genre in Genre.query.all()]
    music_page = request.args.get('page', 1, type=int)
    music_list = Music.query.order_by(Music.upload_date.desc()).paginate(page=music_page, per_page=9)
    music_creators = [User.query.get(music.creator_id).username for music in music_list.items]
    return render_template('music_library.html', music_list=music_list, genres=genres, music_creators = music_creators)

# Filter Music by Genre
@bp.route("/music/genre/<genre>")
def filteredsearch(genre):
    genres = [genre.name for genre in Genre.query.all()]
    genre_obj = Genre.query.filter_by(name=genre).first()
    if not genre_obj:
        flash("Genre not found!", "danger")
        return redirect(url_for('main.music_library'))
    
    music_page = request.args.get('page', 1, type=int)
    music_list = Music.query.filter_by(genre_id=genre_obj.id).paginate(page=music_page, per_page=9)
    music_creators = [User.query.get(music.creator_id).username for music in music_list.items]
    return render_template('music_library.html', music_list=music_list, genres=genres, music_creators = music_creators)

# Listen Music
@bp.route("/music/<int:music_id>")
def get_music(music_id):
    music = Music.query.get_or_404(music_id)
    metrics = MusicMetrics.query.filter_by(music_id=music_id).first()
    music_creator = User.query.get(music.creator_id).username

    # Increment view count
    music_metrics = MusicMetrics.query.filter_by(music_id=music_id).first()
    if music_metrics:
        music_metrics.view_count += 1
        db.session.commit()  # Save the updated view count

    return render_template('music.html', title=music.title, music=music, music_creator = music_creator, metrics = metrics)

@bp.route("/music/<int:music_id>/like", methods=["POST"])
@login_required
def like_music(music_id):
    music = Music.query.get_or_404(music_id)
    metrics = MusicMetrics.query.filter_by(music_id=music.id).first()

    if not metrics:
        metrics = MusicMetrics(music_id=music.id)
        db.session.add(metrics)
        db.session.commit()

    metrics.like_count += 1
    db.session.commit()

    return jsonify({"message": "You liked this song!", "likes": metrics.like_count})

@bp.route("/music/<int:music_id>/dislike", methods=["POST"])
@login_required
def dislike_music(music_id):
    music = Music.query.get_or_404(music_id)
    metrics = MusicMetrics.query.filter_by(music_id=music.id).first()

    if not metrics:
        metrics = MusicMetrics(music_id=music.id)
        db.session.add(metrics)
        db.session.commit()

    metrics.dislike_count += 1
    db.session.commit()

    return jsonify({"message": "You disliked this song!", "dislikes": metrics.dislike_count})

@bp.route("/music/<int:music_id>/save", methods=["POST"])
@login_required
def save_music(music_id):
    music = Music.query.get_or_404(music_id)

    # Check if user already has a playlist
    playlist = Playlist.query.filter_by(user_id=current_user.id).first()

    if not playlist:
        playlist = Playlist(name="My Playlist", user_id=current_user.id)
        db.session.add(playlist)
        db.session.commit()  

    # Check if the music is already in the playlist
    playlist_music = PlaylistMusic.query.filter_by(playlist_id=playlist.id, music_id=music.id).first()

    if not playlist_music:
        playlist_music = PlaylistMusic(playlist_id=playlist.id, music_id=music.id)
        db.session.add(playlist_music)
        db.session.commit()
        return jsonify({"message": "Music saved to playlist!"})

    return jsonify({"message": "Music already in playlist!"})
    
@bp.route("/add_comment/<int:music_id>", methods=["POST"])
@login_required
def add_comment(music_id):
    # Save the comment
    new_comment = Comment(user_id=current_user.id, music_id=music_id, content = request.form["comment"],  date = datetime.utcnow())
    db.session.add(new_comment)
    db.session.commit()
    
    flash("Your comment was sent to the creator!", "success")
    return redirect(url_for("main.get_music", music_id=music_id))

# View Music Playlist
@bp.route("/my_playlist")
@login_required
def playlist():
    # Fetch or create the user's playlist
    playlist = Playlist.query.filter_by(user_id=current_user.id).first()
    
    if not playlist:
        playlist = Playlist(name="My Playlist", user_id=current_user.id)
        db.session.add(playlist)
        db.session.commit()  

    # Get all music IDs from the user's playlist
    playlist_music = PlaylistMusic.query.filter_by(playlist_id=playlist.id).all()
    print(playlist_music)
    music_ids = [pm.music_id for pm in playlist_music]  # Extract music_id values
    
    # Fetch the actual Music objects
    music_list = Music.query.filter(Music.id.in_(music_ids)).all()
    print(music_list)
    # Get creators' names for each music
    music_creators = [User.query.get(music.creator_id).username for music in music_list]
    
    return render_template('playlist.html', music_list=music_list, music_creators=music_creators)


# Music Detail
@bp.route("/music/<int:music_id>/detail")
def music_detail(music_id):
    music = Music.query.get_or_404(music_id)
    music_creator = User.query.get(music.creator_id).username
    metrics = MusicMetrics.query.get(music_id)
    
    comments = Comment.query.filter_by(music_id=music.id).all()
    commentors = [User.query.get(comment.user_id).username for comment in comments]
    
    if not metrics:
        metrics = MusicMetrics(music_id=music.id)
        db.session.add(metrics)
        db.session.commit()

    # Calculate the number of days since release
    days_since_release = (datetime.utcnow().date() - music.upload_date).days
    days_since_release = max(days_since_release, 1)  # Prevent division by zero

    # Calculate averages
    avg_views_per_day = round(metrics.view_count / days_since_release, 2)
    avg_likes_per_day = round(metrics.like_count / days_since_release, 2)
    avg_dislikes_per_day = round(metrics.dislike_count / days_since_release, 2)

    return render_template(
        "musicdetail.html",
        music=music,
        music_creator=music_creator,
        music_metrics=metrics,
        avg_views_per_day=avg_views_per_day,
        avg_likes_per_day=avg_likes_per_day,
        avg_dislikes_per_day=avg_dislikes_per_day,
        comments = comments,
        commentors = commentors
    )

# Delete Music (Only for Creator)  
@bp.route("/music/<int:music_id>/delete", methods=['POST'])
@login_required
def delete_music(music_id):
    music = Music.query.get_or_404(music_id)
    metrics = MusicMetrics.query.filter_by(music_id=music.id).first()
    
    if music.creator_id != current_user.id:
        abort(403)  # Forbidden access
    
    db.session.delete(music)
    db.session.delete(metrics)
    db.session.commit()
    flash('Music has been deleted!', 'success')
    
    return redirect(url_for('main.music_library'))


