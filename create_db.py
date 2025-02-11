# create_db.py
from musicapp import create_app, db
from musicapp.models import Genre

app = create_app()

# Push the application context
with app.app_context():
    # Create all database tables
    db.drop_all()
    db.create_all()

    # Add sample genres
    genres = ['Rock', 'Pop', 'Jazz', 'Classical' , 'Others']
    for genre_name in genres:
        genre = Genre(name=genre_name)
        db.session.add(genre)
    
    # Commit the changes
    db.session.commit()
    print("Database tables created and sample data added successfully!")