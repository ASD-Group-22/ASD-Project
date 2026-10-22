from .student import Student
from .project_requirement import ProjectRequirement
from .group import Group

# Keep these public model exports and their SQLAlchemy table registration.
__all__ = ['Student', 'ProjectRequirement', 'Group']
