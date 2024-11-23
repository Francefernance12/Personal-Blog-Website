from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


# CREATE DATABASE BASE
class Base(DeclarativeBase):
    pass


# Parent
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    # relationship
    role_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("roles.id"), nullable=False)
    # relationship
    role = relationship("Roles", back_populates="user")
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comments", back_populates="comment_author")

    # Generate hash/salted password method
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, salt_length=8)

    # Method checks if the provided password matches the stored hash.
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'{self.username}'


# CONFIGURE TABLES
# Child of User
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(500), nullable=False)
    creation_date: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    # foreign key
    author_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Relationship with User/Comments
    author = relationship("User", back_populates="posts")
    comments = relationship("Comments", back_populates="parent_post")


# Comments db
# Child of User
class Comments(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # relationship with User
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # Relationship with BlogPost
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


# User's roles
class Roles(db.Model):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), unique=False, nullable=True)
    # Permissions
    can_make_posts: Mapped[bool] = mapped_column(Boolean, default=False)
    can_edit_posts: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete_posts: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_comment: Mapped[bool] = mapped_column(Boolean, default=False)
    can_comment: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete_comment: Mapped[bool] = mapped_column(Boolean, default=False)

    # relationship
    user = relationship("User", back_populates="role")


