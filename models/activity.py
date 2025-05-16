from .database import get_db

class Activity:
    def __init__(self, user_id=None, activity_type=None, description=None):
        self.user_id = user_id
        self.activity_type = activity_type
        self.description = description

    def create(self):
        """创建新的活动记录"""
        db = get_db()
        try:
            cursor = db.execute('''
                INSERT INTO user_activities (user_id, activity_type, description)
                VALUES (?, ?, ?)
            ''', (self.user_id, self.activity_type, self.description))
            activity_id = cursor.lastrowid
            db.commit()
            db.close()
            return activity_id
        except Exception as e:
            db.rollback()
            db.close()
            raise e

    @staticmethod
    def get_user_activities(user_id, limit=10):
        """获取用户的活动记录"""
        db = get_db()
        activities = db.execute('''
            SELECT * FROM user_activities 
            WHERE user_id = ? 
            ORDER BY create_time DESC
            LIMIT ?
        ''', (user_id, limit)).fetchall()
        db.close()
        return activities

    @staticmethod
    def delete_user_activities(user_id):
        """删除用户的所有活动记录"""
        db = get_db()
        try:
            db.execute('DELETE FROM user_activities WHERE user_id = ?', (user_id,))
            db.commit()
            db.close()
            return True
        except Exception as e:
            db.rollback()
            db.close()
            raise e 