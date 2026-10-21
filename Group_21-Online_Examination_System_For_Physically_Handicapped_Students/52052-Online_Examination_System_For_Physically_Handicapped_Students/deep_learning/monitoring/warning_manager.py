import time
from database import get_connection


class WarningManager:

    last_warning_time = {}
    exam_warning_count = {}
    candidate_by_student = {}

    COOLDOWN = 10
    REQUIRED_CONFIRMATIONS = 2

    @classmethod
    def reset_student(cls, student_id):
        key = str(student_id)
        cls.exam_warning_count[key] = 0
        cls.last_warning_time.pop(key, None)
        cls.candidate_by_student.pop(key, None)

    @classmethod
    def clear_candidate(cls, student_id):
        cls.candidate_by_student.pop(str(student_id), None)

    @classmethod
    def current_count(cls, student_id):
        return cls.exam_warning_count.get(str(student_id), 0)

    def add_warning(self, student_id, reason):

        current_time = time.time()

        key = str(student_id)

        candidate_reason, candidate_count = self.candidate_by_student.get(key, (None, 0))
        if candidate_reason == reason:
            candidate_count += 1
        else:
            candidate_count = 1
        self.candidate_by_student[key] = (reason, candidate_count)

        if candidate_count < self.REQUIRED_CONFIRMATIONS:
            return self.exam_warning_count.get(key, 0)

        self.candidate_by_student.pop(key, None)

        if key in self.last_warning_time:

            if current_time - self.last_warning_time[key] < self.COOLDOWN:

                return self.exam_warning_count.get(key, 0)

        self.last_warning_time[key] = current_time

        connection = get_connection()

        cursor = connection.cursor()

        warning = self.exam_warning_count.get(key, 0) + 1
        self.exam_warning_count[key] = warning

        cursor.execute(
            """
            INSERT INTO exam_warnings
            (
                student_id,
                warning_number,
                reason
            )
            VALUES(%s,%s,%s)
            """,
            (
                student_id,
                warning,
                reason
            )
        )

        connection.commit()

        cursor.close()

        connection.close()

        return warning
