import enum


class UserRole(str, enum.Enum):
    director = "director"
    teacher = "teacher"
    student = "student"


class HomeworkStatus(str, enum.Enum):
    pending = "pending"
    ai_reviewed = "ai_reviewed"
    teacher_reviewed = "teacher_reviewed"


class NoiseSessionStatus(str, enum.Enum):
    recording = "recording"
    processing = "processing"
    ready = "ready"
