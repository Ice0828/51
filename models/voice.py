from .database import get_db

class Voice:
    def __init__(self, user_id=None, voice_uri=None, voice_name=None, custom_name=None, voice_description=None):
        self.user_id = user_id
        self.voice_uri = voice_uri
        self.voice_name = voice_name
        self.custom_name = custom_name
        self.voice_description = voice_description

    def create(self):
        """创建新的语音记录"""
        db = get_db()
        try:
            cursor = db.execute('''
                INSERT INTO user_voices (user_id, voice_uri, voice_name, custom_name, voice_description)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, self.voice_uri, self.voice_name, self.custom_name, self.voice_description))
            voice_id = cursor.lastrowid
            db.commit()
            db.close()
            return voice_id
        except Exception as e:
            db.rollback()
            db.close()
            raise e

    @staticmethod
    def get_user_voices(user_id):
        """获取用户的所有语音"""
        db = get_db()
        voices = db.execute('''
            SELECT * FROM user_voices 
            WHERE user_id = ? 
            ORDER BY create_time DESC
        ''', (user_id,)).fetchall()
        db.close()
        return voices

    @staticmethod
    def get_by_id(voice_id):
        """通过ID获取语音"""
        db = get_db()
        voice = db.execute('SELECT * FROM user_voices WHERE id = ?', (voice_id,)).fetchone()
        db.close()
        return voice if voice else None

    @staticmethod
    def update_name(voice_id, custom_name):
        """更新语音名称"""
        db = get_db()
        try:
            db.execute('UPDATE user_voices SET custom_name = ? WHERE id = ?', (custom_name, voice_id))
            db.commit()
            db.close()
            return True
        except Exception as e:
            db.rollback()
            db.close()
            raise e

    @staticmethod
    def delete(voice_id):
        """删除语音"""
        db = get_db()
        try:
            db.execute('DELETE FROM user_voices WHERE id = ?', (voice_id,))
            db.commit()
            db.close()
            return True
        except Exception as e:
            db.rollback()
            db.close()
            raise e 