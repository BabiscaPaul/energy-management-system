import enum

class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    CLIENT = "client"