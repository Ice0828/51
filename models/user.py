from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db

class User:
    def __init__(self, id=None, username=None, email=None, password=None):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def get_by_id(user_id):
        """通过ID获取用户"""
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        db.close()
        return user if user else None

    @staticmethod
    def get_by_email(email):
        """通过邮箱获取用户"""
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        return user if user else None

    @staticmethod
    def get_by_username(username):
        """通过用户名获取用户"""
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()
        return user if user else None

    def create(self):
        """创建新用户"""
        db = get_db()
        try:
            cursor = db.execute(
                'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                (self.username, generate_password_hash(self.password), self.email)
            )
            user_id = cursor.lastrowid
            db.commit()
            db.close()
            return user_id
        except Exception as e:
            db.rollback()
            db.close()
            raise e

    @staticmethod
    def update_profile(user_id, data):
        """更新用户信息"""
        db = get_db()
        try:
            db.execute('''
                UPDATE users 
                SET phone = ?, address = ?, nationality = ?, native_language = ?
                WHERE id = ?
            ''', (data.get('phone'), data.get('address'), 
                  data.get('nationality'), data.get('native_language'), user_id))
            db.commit()
            db.close()
            return True
        except Exception as e:
            db.rollback()
            db.close()
            raise e

    @staticmethod
    def delete(user_id):
        """删除用户"""
        db = get_db()
        try:
            db.execute('DELETE FROM users WHERE id = ?', (user_id,))
            db.commit()
            db.close()
            return True
        except Exception as e:
            db.rollback()
            db.close()
            raise e

    @staticmethod
    def verify_password(stored_password_hash, password):
        """验证密码"""
        return check_password_hash(stored_password_hash, password) 