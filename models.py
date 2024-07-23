from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column, column_property
from sqlalchemy import Integer, String, Boolean, ForeignKey, Float, Date, CheckConstraint, DateTime, Table, Column
from datetime import datetime, time

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
db = SQLAlchemy(model_class=Base)


# CONFIGURE TABLES
# Many to many relationship tables:
# Many-to-many relationship between Users and Stages
user_project_stages = Table(
    'user_project_stages',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('project_stage_id', Integer, ForeignKey('stages.id')),
    Column('employee_id', Integer, ForeignKey('users.id'))
)

# Many-to-many relationship between Employees and JobsHistory
jobs_history_employees = Table(
    'jobs_history_employees',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('job_history_id', Integer, ForeignKey('jobs_history.id')),
    Column('employee_id', Integer, ForeignKey('employees.id'))
)



# Basics:
class Unit(db.Model):
    __tablename__ = "units"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), unique=True, nullable=False)
    description = mapped_column(String(100))


# Project:
class Project(db.Model):
    __tablename__ = "projects"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), nullable=False, unique=True)
    slogan = mapped_column(String(250), nullable=False)
    description = mapped_column(String(250), nullable=False)
    start_date = mapped_column(Date, nullable=False)
    end_date = mapped_column(Date, nullable=False)
    img = mapped_column(String(255), default="../static/assets/img/default-profile.jpg")
    stages = relationship('Stage', backref='project', lazy=True)

class Stage(db.Model):
    __tablename__ = "stages"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), nullable=False)
    slogan = mapped_column(String(250))
    description = mapped_column(String(250))
    img = mapped_column(String(255), default="../static/assets/img/default-profile.jpg")
    start_date = mapped_column(Date, nullable=False)
    end_date = mapped_column(Date, nullable=False)
    project_id = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    phases = relationship('Phase', backref='stage_relation', lazy=True)
    user_entries = relationship('User', secondary=user_project_stages, backref='stages')

class Phase(db.Model):
    __tablename__ = "phases"
    id = mapped_column(Integer, primary_key=True)
    stage = relationship('Stage')
    name = mapped_column(String(250), nullable=False)
    description = mapped_column(String(250))
    stage_id = mapped_column(Integer, ForeignKey('stages.id'), nullable=False)
    concepts_relation = relationship('Concept', backref='phase_relation', lazy=True)
    code = mapped_column(String(5))

class Concept(db.Model):
    __tablename__ = "concepts"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), nullable=False)
    description = mapped_column(String(250))
    quantity = mapped_column(Float(250))
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    phase_id = mapped_column(Integer, ForeignKey('phases.id'), nullable=False)
    phase = relationship('Phase')
    code = mapped_column(String(20))

    # Relationships with generator tables
    mat_generators = relationship('MatGenerator', backref='concept', lazy=True)
    mo_generators = relationship('MoGenerator', backref='concept', lazy=True)
    maq_generators = relationship('MaqGenerator', backref='concept', lazy=True)
    her_generators = relationship('HerGenerator', backref='concept', lazy=True)

    # Custom constructor to generate concept code
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.code:
            phase_code = self.phase.code
            position = len(self.phase.concepts)
            self.code = f"{phase_code}-{position+1}"


# Assets:
class Tool(db.Model):
    __tablename__ = "tools"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), unique=True, nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    price = mapped_column(Float, nullable=False)
    last_update = mapped_column(Date, nullable=False)

class Job(db.Model):
    __tablename__ = "jobs"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), unique=True, nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    price = mapped_column(Float, nullable=False)
    last_update = mapped_column(Date, nullable=False)

class Machinery(db.Model):
    __tablename__ = "machineries"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), unique=True, nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    price = mapped_column(Float, nullable=False)
    last_update = mapped_column(Date, nullable=False)

class Material(db.Model):
    __tablename__ = "materials"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), unique=True, nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    price = mapped_column(Float, nullable=False)
    last_update = mapped_column(Date, nullable=False)


# Generator tables:
class MatGenerator(db.Model):
    __tablename__ = "mat_generators"
    id = mapped_column(Integer, primary_key=True)
    material_id = mapped_column(Integer, ForeignKey('materials.id'), nullable=False)
    name = relationship('Material', foreign_keys=[material_id], backref='mat_generators')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    concept_id = mapped_column(Integer, ForeignKey('concepts.id'), nullable=False)

class MoGenerator(db.Model):
    __tablename__ = "mo_generators"
    id = mapped_column(Integer, primary_key=True)
    job_id = mapped_column(Integer, ForeignKey('jobs.id'), nullable=False)
    name = relationship('Job', foreign_keys=[job_id], backref='mo_generators')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    concept_id = mapped_column(Integer, ForeignKey('concepts.id'), nullable=False)

class MaqGenerator(db.Model):
    __tablename__ = "maq_generators"
    id = mapped_column(Integer, primary_key=True)
    machinery_id = mapped_column(Integer, ForeignKey('machineries.id'), nullable=False)
    name = relationship('Machinery', foreign_keys=[machinery_id], backref='maq_generators')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    concept_id = mapped_column(Integer, ForeignKey('concepts.id'), nullable=False)

class HerGenerator(db.Model):
    __tablename__ = "her_generators"
    id = mapped_column(Integer, primary_key=True)
    tool_id = mapped_column(Integer, ForeignKey('tools.id'), nullable=False)
    name = relationship('Tool', foreign_keys=[tool_id], backref='her_generators')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    concept_id = mapped_column(Integer, ForeignKey('concepts.id'), nullable=False)


# Inventory:
class Locations(db.Model):
    __tablename__ = "locations"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), nullable=False, unique=True)
    stage_id = mapped_column(Integer, ForeignKey('stages.id'), nullable=False)  # Foreign key to Stages table
    stage = relationship('Stage')  # Relationship to Stages table

# Materials Inventory:
class MaterialEntry(db.Model):
    __tablename__ = "material_entries"
    id = mapped_column(Integer, primary_key=True)
    entry_date = mapped_column(Date, nullable=False)
    material_id = mapped_column(Integer, ForeignKey('materials.id'), nullable=False)
    material = relationship('Material')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    destination_location_id = mapped_column(Integer, ForeignKey('locations.id'), nullable=False)
    destination_location = relationship('Locations')
    price = mapped_column(Float, nullable=False)
    total = mapped_column(Float)
    employee_id = mapped_column(Integer, ForeignKey('employees.id'), nullable=False)
    responsible_employee = relationship('Employee')

class MaterialMove(db.Model):
    __tablename__ = "material_moves"
    id = mapped_column(Integer, primary_key=True)
    move_date = mapped_column(Date, nullable=False)
    material_id = mapped_column(Integer, ForeignKey('materials.id'), nullable=False)
    material = relationship('Material')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    source_location_id = mapped_column(Integer, ForeignKey('locations.id'), nullable=False)
    source_location = relationship('Locations', foreign_keys=[source_location_id])
    destination_location_id = mapped_column(Integer, ForeignKey('locations.id'), nullable=False)
    destination_location = relationship('Locations', foreign_keys=[destination_location_id])
    employee_id = mapped_column(Integer, ForeignKey('employees.id'), nullable=False)
    responsible_employee = relationship('Employee')

class MaterialExit(db.Model):
    __tablename__ = "material_exits"
    id = mapped_column(Integer, primary_key=True)
    exit_date = mapped_column(Date, nullable=False)
    material_id = mapped_column(Integer, ForeignKey('materials.id'), nullable=False)
    material = relationship('Material')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    concept_id = mapped_column(Integer, ForeignKey('concepts.id'), nullable=False)
    concept = relationship('Concept')
    employee_id = mapped_column(Integer, ForeignKey('employees.id'), nullable=False)
    responsible_employee = relationship('Employee')

# Tools Inventory:
class ToolEntry(db.Model):
    __tablename__ = "tool_entries"
    id = mapped_column(Integer, primary_key=True)
    entry_date = mapped_column(Date, nullable=False)
    tool_id = mapped_column(Integer, ForeignKey('tools.id'), nullable=False)
    tool = relationship('Tool')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    destination_location_id = mapped_column(Integer, ForeignKey('locations.id'), nullable=False)
    destination_location = relationship('Locations')
    price = mapped_column(Float, nullable=False)
    total = mapped_column(Float)
    employee_id = mapped_column(Integer, ForeignKey('employees.id'), nullable=False)
    responsible_employee = relationship('Employee')

class ToolMove(db.Model):
    __tablename__ = "tool_moves"
    id = mapped_column(Integer, primary_key=True)
    move_date = mapped_column(Date, nullable=False)
    tool_id = mapped_column(Integer, ForeignKey('tools.id'), nullable=False)
    tool = relationship('Tool')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    source_location_id = mapped_column(Integer, ForeignKey('locations.id'), nullable=False)
    source_location = relationship('Locations', foreign_keys=[source_location_id])
    destination_location_id = mapped_column(Integer, ForeignKey('locations.id'), nullable=False)
    destination_location = relationship('Locations', foreign_keys=[destination_location_id])
    employee_id = mapped_column(Integer, ForeignKey('employees.id'), nullable=False)
    responsible_employee = relationship('Employee')

class ToolExit(db.Model):
    __tablename__ = "tool_exits"
    id = mapped_column(Integer, primary_key=True)
    exit_date = mapped_column(Date, nullable=False)
    tool_id = mapped_column(Integer, ForeignKey('tools.id'), nullable=False)
    tool = relationship('Tool')
    quantity = mapped_column(Float(250), nullable=False)
    unit_id = mapped_column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    concept_id = mapped_column(Integer, ForeignKey('concepts.id'), nullable=False)
    concept = relationship('Concept')
    employee_id = mapped_column(Integer, ForeignKey('employees.id'), nullable=False)
    responsible_employee = relationship('Employee')


# Purchase:
class Providor(db.Model):
    __tablename__ = "providors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(250))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    phone: Mapped[str] = mapped_column(String(100), unique=True)
    profile_picture: Mapped[str] = mapped_column(String(255), default="../static/assets/img/default-profile.jpg")  # Adjust the length as needed
    description: Mapped[str] = mapped_column(String(250), nullable=False)

class MaqRental(db.Model):
    __tablename__ = "machinery_rentals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    machinery_id = mapped_column(Integer, ForeignKey('machineries.id'), nullable=False)
    machinery = relationship('Machinery')
    providor_id = mapped_column(Integer, ForeignKey('providors.id'), nullable=False)
    providor = relationship('Providor')
    concept_id = mapped_column(Integer, ForeignKey('concepts.id'), nullable=False)
    concept = relationship('Concept')

# Sale:
class Client(db.Model):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(250))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    phone: Mapped[str] = mapped_column(String(100), unique=True)
    profile_picture: Mapped[str] = mapped_column(String(255), default="../static/assets/img/default-profile.jpg")  # Adjust the length as needed
    description: Mapped[str] = mapped_column(String(250), nullable=False)


# HR
class Investor(db.Model):
    __tablename__ = "investors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    phone: Mapped[str] = mapped_column(String(100), unique=True)
    profile_picture: Mapped[str] = mapped_column(String(255), default="../static/assets/img/default-profile.jpg")  # Adjust the length as needed
    investment: Mapped[float] = mapped_column(Float, nullable=False)

class Attendance(db.Model):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    entry_hour = Column(DateTime, nullable=False, default=datetime.now().replace(minute=0, second=0, microsecond=0))
    exit_hour = Column(DateTime, nullable=False, default=datetime.combine(datetime.today(), time(18, 0)))
    employee = relationship('Employee', back_populates='attendances')

class Employee(db.Model):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(100), unique=True)
    profile_picture = Column(String(255), default="../static/assets/img/default-profile.jpg")
    rank = Column(String(255), nullable=False)
    specialty_id = Column(Integer, ForeignKey('specialties.id'), nullable=False)
    specialty = relationship('Specialty')
    base_salary = Column(Float, nullable=False)
    last_update = Column(Date, nullable=False)
    jobs_history_entries = relationship('JobsHistory', secondary=jobs_history_employees, backref='employees')
    attendances = relationship('Attendance', back_populates='employee')

    __table_args__ = (
        CheckConstraint(rank.in_(['Maestro', 'Chalan']), name='check_rank_values'),
    )

# Define the JobsHistory class
class JobsHistory(db.Model):
    __tablename__ = "jobs_history"
    id = Column(Integer, primary_key=True)
    concept_id = Column(Integer, ForeignKey('concepts.id'), nullable=False)
    concept = relationship('Concept')
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    job = relationship('Job')
    description = Column(String(250), nullable=False)
    quantity = Column(Float(250), nullable=False)
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=False)
    unit = relationship('Unit')
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    employee_entries = relationship('Employee', secondary=jobs_history_employees, backref='jobs_history')

class Specialty(db.Model):
    __tablename__ = "specialties"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), nullable=False)
    description = mapped_column(String(250), nullable=False)

class NewUser(db.Model):
    __tablename__ = "new_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(100), default='Pending')
    profile_picture: Mapped[str] = mapped_column(String(255), default="../static/assets/img/default-profile.jpg")  # Adjust the length as needed

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    gram: Mapped[str] = mapped_column(String(100), unique=True)
    profile_picture: Mapped[str] = mapped_column(String(255), default="../static/assets/img/default-profile.jpg")  # Adjust the length as needed
    is_admin: Mapped[bool] = mapped_column(Boolean)
    about: Mapped[str] = mapped_column(String(255), default='')
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=False)
    position = relationship('Position')
    project_stage_entries = relationship('Stage', secondary=user_project_stages, backref='users')


class Position(db.Model):
    __tablename__ = "positions"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(250), nullable=False, unique=True)
    description = mapped_column(String(250), nullable=False)


# Files
class File(db.Model):
    __tablename__='files'
    id = mapped_column(Integer, primary_key=True)
    file_type = mapped_column(String(250), nullable=False, unique=True)
    file_path = mapped_column(String(250), nullable=False, unique=True)
    # If file_type is Laboratory Results, Autocad or Revit model, it has to be related to at least one of the following: project, stage, concept and/or any generators.
    # If file_type is Licence, Permit, Plan, Render, or Video it has to be related to a project, and optionaly can be related to a stage.
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship('Project')
    stage_id = Column(Integer, ForeignKey('stages.id'))
    stage = relationship('Stage')
    # If file_type is Diagram, it has to be related to a concept, and optionaly can be related to a generator.
    concept_id = Column(Integer, ForeignKey('concepts.id'))
    concept = relationship('Concept')
    matgenerator_id = Column(Integer, ForeignKey('mat_generators.id'))
    matgenerator = relationship('MatGenerator')
    mogenerator_id = Column(Integer, ForeignKey('mo_generators.id'))
    mogenerator = relationship('MoGenerator')
    maqgenerator_id = Column(Integer, ForeignKey('maq_generators.id'))
    maqgenerator = relationship('MaqGenerator')
    herenerator_id = Column(Integer, ForeignKey('her_generators.id'))
    hergenerator = relationship('HerGenerator')
    # If file_type is Contract, Invoice or Advance it has to be related to at least one of the following: employee, providor, client.
    providor_id = Column(Integer, ForeignKey('providors.id'))
    providor = relationship('Providor')
    client_id = Column(Integer, ForeignKey('clients.id'))
    client = relationship('Client')
    # If file_type is Payroll, it has to be related to an employee.
    employee_id = Column(Integer, ForeignKey('employees.id'))
    employee = relationship('Employee')
    # If file_type is Payroll, Licence or Permit it has to have a start and end date, and if it is an invoice it has to have a start date.
    start_date = mapped_column(Date)
    end_date = mapped_column(Date)
    # If file_type is Invoice or Note it has to be related to at least one of the following:
    materialentry_id = Column(Integer, ForeignKey('material_entries.id'))
    materialentry = relationship('MaterialEntry')
    materialexit_id = Column(Integer, ForeignKey('material_exits.id'))
    materialexit = relationship('MaterialExit')
    toolentry_id = Column(Integer, ForeignKey('tool_entries.id'))
    toolentry = relationship('ToolEntry')
    toolexit_id = Column(Integer, ForeignKey('tool_exits.id'))
    toollexit = relationship('ToolExit')
    maqrental_id = Column(Integer, ForeignKey('machinery_rentals.id'))
    maqrental = relationship('MaqRental')

