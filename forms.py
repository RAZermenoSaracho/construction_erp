from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField, SelectField, RadioField, BooleanField, FloatField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField
from flask import request, session, flash
import pandas as pd
from flask_wtf.file import FileField

from sqlalchemy import Integer, String, Boolean, Float, Date, DateTime
from sqlalchemy import inspect
from models import db, Unit, Project, Stage, Phase, Concept, Tool, Job, Machinery, Material, MatGenerator, MoGenerator, MaqGenerator, HerGenerator, Locations, MaterialEntry, MaterialMove, MaterialExit, ToolEntry, ToolMove, ToolExit, Providor, MaqRental, Investor, jobs_history_employees, Employee, JobsHistory, Specialty, NewUser, User, Position, File


class SelectModelForm(FlaskForm):
    model = SelectField("Model", validators=[DataRequired()])
    select = SubmitField("Select")

def create_new_record_form(model):
    class CreateNewRecordForm(FlaskForm):
        pass
    
    inspector = inspect(model)
    columns = inspector.columns.values()
    
    for column in columns:
        if column.primary_key:
            continue
        
        column_name = column.name.capitalize().replace('_',' ')

        if 'img' in column.name or 'picture' in column.name or 'file' in column.name or 'path' in column.name:
            field = FileField(column_name)
        elif '_id' in column.name:
            column_name = column.name.capitalize().replace('_id','')
            # Set choices for the select field based on related model
            related_model_name = column.name.replace('_id','').capitalize()  # Remove '_id' suffix
            query = f'{related_model_name}.query.all()'
            records = eval(query)
            choices = [(record.id, record.name) for record in records]
            field = SelectField(column_name, validators=[DataRequired()], choices=choices)
        elif 'description' in column.name:
            field = CKEditorField(column_name, validators=[DataRequired()])
        elif isinstance(column.type, Integer):
            field = StringField(column_name, validators=[DataRequired()])
        elif isinstance(column.type, String):
            field = StringField(column_name, validators=[DataRequired()])
        elif isinstance(column.type, Boolean):
            field = BooleanField(column_name)
        elif isinstance(column.type, Float):
            field = FloatField(column_name, validators=[DataRequired()])
        elif isinstance(column.type, Date):
            field = DateField(column_name, validators=[DataRequired()])
        elif isinstance(column.type, DateTime):
            field = DateTimeField(column_name, validators=[DataRequired()])
        else:
            # Handle other column types as needed
            field = StringField(column.name)
        
        setattr(CreateNewRecordForm, column.name, field)

    # Add submit field
    submit = SubmitField('Submit')
    setattr(CreateNewRecordForm, 'submit', submit)

    return CreateNewRecordForm()


class ConceptCatalogSelector(FlaskForm):
    project = SelectField("Project", validators=[DataRequired()])
    stage = SelectField("Stage", validators=[DataRequired()])
    select = SubmitField("Select")


class CreateProjectForm(FlaskForm):
    name = StringField("Project Name", validators=[DataRequired()])
    slogan = StringField("Project Slogan", validators=[DataRequired()])
    img = FileField("Project Front Image")
    description = CKEditorField("Project's Description", validators=[DataRequired()])
    start_date = DateField("Estimated Start Date", format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField("Estimated End Date", format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField("Create Project")


class CreateStageForm(FlaskForm):
    name = StringField("Stage Name", validators=[DataRequired()])
    slogan = StringField("Stage Slogan")
    img = FileField("Stage Front Image")
    description = CKEditorField("Stage's Description")
    start_date = DateField("Estimated Start Date", format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField("Estimated End Date", format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField("Create Stage")


class CreatePhaseForm(FlaskForm):
    name = StringField("Phase Name", validators=[DataRequired()])
    description = CKEditorField("Phase's Description")
    submit = SubmitField("Create Phase")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Register")

class EditUserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    is_admin = SelectField("Is admin", choices=[(True, 'True'), (False, 'False')], validators=[DataRequired()])
    gram = StringField("GRAM", validators=[DataRequired()])
    position = SelectField("Position", validators=[DataRequired()])
    profile_picture = FileField("Profile Picture")
    about = CKEditorField("About")
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password")
    submit = SubmitField("Submit Changes")

# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

def create_filtering_form(column_choices):
    class FilteringForm(FlaskForm):
        column = SelectField('Column', choices=column_choices)
        condition = SelectField('Condition', choices=[('==', '='), ('!=', '!='), ('<=', '<='), ('<', '<'), ('>=', '>='), ('>', '>'), ('contains', 'contains')], default='contains')
        input = StringField('Input')
        logical_operator = RadioField('Logical Operator', choices=[('&', 'and'), ('|', 'or')], default='&')
        add_filter = SubmitField('Add Filter')
        queries = CKEditorField("Queries")
        apply = SubmitField('Apply Filters')

    return FilteringForm()


class SelfFilteringTable:
    def __init__(self, df, columns, column_types):
        self.df = df
        self.columns = columns
        self.column_types = column_types
        self.form = create_filtering_form(self.columns)
        self.process = self.process_request()
    
    def process_request(self):
        if request.method == 'GET' or 'filtering_inputs' not in session:
            self.initialize_session()
        else:
            if 'add_filter' in request.form:
                self.load_session()
                self.add_filter()
                self.form.queries.data = self.filtering_inputs  # Update queries field
            elif 'apply' in request.form:
                self.filtering_inputs = self.form.queries.data
                session['filtering_inputs'] = self.filtering_inputs
            elif 'sort_column' in request.form and 'sort_direction' in request.form:
                self.sort_column = request.form.get('sort_column')
                session['sort_column'] = self.sort_column
                self.sort_direction = request.form.get('sort_direction')
                session['sort_direction'] = self.sort_direction
            
            self.load_session()

        self.table = self.apply_filters()

    def initialize_session(self):
        if not self.df.empty:  # Check if DataFrame is not empty
            self.sort_column = self.df.columns[0]  # Access first column only if DataFrame is not empty
            session['sort_column'] = self.sort_column
        else:
            self.sort_column = None
            session['sort_column'] = None

        self.filtering_inputs = ''
        session['filtering_inputs'] = self.filtering_inputs
        self.sort_direction = 'asc'
        session['sort_direction'] = self.sort_direction


    def load_session(self):
        self.filtering_inputs = session['filtering_inputs']
        self.sort_column = session['sort_column']
        self.sort_direction = session['sort_direction']

    def add_filter(self):
        column = self.form.column.data
        condition = self.form.condition.data
        input_data = self.form.input.data
        logical_operator = self.form.logical_operator.data
        column_type = self.column_types[self.columns.index(column)]

        if input_data:
            try:
                converted_input = column_type(input_data)  # Try to convert input_data to the column_type
            except ValueError:
                converted_input = None
            
            if condition == 'contains':
                if column_type == str:
                    df_query = f'(self.df["{column}"].str.contains("{input_data}"))'
                else:
                    df_query = f'(self.df["{column}"].astype(str).str.contains("{input_data}"))'
            else:
                df_query = f'(self.df["{column}"]{condition}{converted_input})'

            if converted_input is None:
                flash(f'The input type is not correct, it should be {column_type} type.')
            elif df_query not in self.filtering_inputs:
                if len(self.filtering_inputs) == 0:
                    self.filtering_inputs = self.filtering_inputs + df_query
                    session['filtering_inputs'] = self.filtering_inputs
                else:
                    self.filtering_inputs = self.filtering_inputs + logical_operator
                    self.filtering_inputs = self.filtering_inputs + df_query
                    session['filtering_inputs'] = self.filtering_inputs
            else:
                flash('That filter is already considered.')
        else:
            flash("Can't add an empty input.")


    def apply_filters(self):
        if len(self.filtering_inputs)>0:
            self.df = self.df[eval(self.filtering_inputs)]
            table = self.df
        else:
            table = self.df
        
        return self.sort_data(table)


    def sort_data(self, table):
        if not table.empty:
            if self.sort_direction == 'asc':
                table = table.sort_values(by=self.sort_column)
            else:
                table = table.sort_values(by=self.sort_column, ascending=False)
        return table
