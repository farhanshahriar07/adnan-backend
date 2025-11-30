from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Admin User Model (Updated for Email Auth)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# About Me Section
class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    birthday = db.Column(db.String(50))
    website = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    city = db.Column(db.String(50))
    age = db.Column(db.Integer)
    degree = db.Column(db.String(50))
    email = db.Column(db.String(100))
    freelance_status = db.Column(db.String(20))
    short_bio = db.Column(db.Text)
    long_bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255))
    resume_link = db.Column(db.String(255)) # New Field
    
    # Social Links
    github = db.Column(db.String(255))
    facebook = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    whatsapp = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    twitter = db.Column(db.String(255))

    def to_dict(self):
        return {
            'name': self.name,
            'birthday': self.birthday,
            'website': self.website,
            'phone': self.phone,
            'city': self.city,
            'age': self.age,
            'degree': self.degree,
            'email': self.email,
            'freelance_status': self.freelance_status,
            'short_bio': self.short_bio,
            'long_bio': self.long_bio,
            'profile_image': self.profile_image,
            'resume_link': self.resume_link,
            'github': self.github,
            'facebook': self.facebook,
            'linkedin': self.linkedin,
            'whatsapp': self.whatsapp,
            'instagram': self.instagram,
            'twitter': self.twitter
        }

# Skills Section
class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    percentage = db.Column(db.Integer, nullable=False) 

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'percentage': self.percentage
        }

# Education Section
class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    degree = db.Column(db.String(100), nullable=False)
    institution = db.Column(db.String(100), nullable=False)
    year_range = db.Column(db.String(50))
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'degree': self.degree,
            'institution': self.institution,
            'year_range': self.year_range,
            'description': self.description
        }

# Experience Section
class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    year_range = db.Column(db.String(50))
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'company': self.company,
            'year_range': self.year_range,
            'description': self.description
        }

# Projects Section
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50)) 
    image_url = db.Column(db.String(255))
    project_link = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'image_url': self.image_url,
            'project_link': self.project_link
        }

# Thesis Section
class Thesis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    link = db.Column(db.String(255))
    publication_date = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'link': self.link,
            'publication_date': self.publication_date
        }

# Contact Messages
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'subject': self.subject,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'read': self.read
        }