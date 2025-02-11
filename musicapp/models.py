from datetime import datetime
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from musicapp import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')  # 'user' or 'creator'
    bank_details = db.Column(db.String(50), nullable=True)  # Only for creators

    def get_reset_token(self):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.image_file}', '{self.password}')"

# Playlists Table
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Playlist('{self.name}', User ID: {self.user_id})"

# Music Table
class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=False) 
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_image_file = db.Column(db.String(100), nullable=False, default='default_cover.jpg')  # Default cover
    upload_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))
    shareable = db.Column(db.Boolean, default=True)
    premium = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"Music(Title: {self.title}, Creator ID: {self.creator_id}, upload_date: {self.upload_date }, Cover: {self.cover_image_file if self.cover_image_file else 'None'}, Genre_ID: {self.genre_id}, Shareable: {self.shareable}, Premium: {self.premium})"

# Comments Table
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    music_id = db.Column(db.Integer, db.ForeignKey('music.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"Comment(ID: {self.id}, User ID: {self.user_id}, Music ID: {self.music_id}, Content: {self.content[:20]}..., date: {self.date})"

# Membership Table
class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Numeric(8, 2), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Membership(ID: {self.id}, Price: {self.price}, Creator ID: {self.creator_id})"

# Purchased Membership Table
class PurchasedMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    membership_id = db.Column(db.Integer, db.ForeignKey('membership.id'), nullable=False)

    def __repr__(self):
        return f"PurchasedMembership(ID: {self.id}, User ID: {self.user_id}, Membership ID: {self.membership_id})"

# Genre Table
class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Genre('{self.name}')"

# Playlist-Music Relationship Table (Many-to-Many)
class PlaylistMusic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    music_id = db.Column(db.Integer, db.ForeignKey('music.id'), nullable=False)

    def __repr__(self):
        return f"PlaylistMusic(Playlist ID: {self.playlist_id}, Music ID: {self.music_id})"

# Music Metrics Table
class MusicMetrics(db.Model):
    music_id = db.Column(db.Integer, db.ForeignKey('music.id'), primary_key=True)
    like_count = db.Column(db.Integer, default=0)
    dislike_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"MusicMetrics(Music ID: {self.music_id}, Likes: {self.like_count}, Dislikes: {self.dislike_count}, Views: {self.view_count})"
