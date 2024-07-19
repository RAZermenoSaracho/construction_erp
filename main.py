from datetime import date, time
from flask import Flask, abort, render_template, redirect, url_for, flash, request, session
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import os
import shutil
from sqlalchemy import inspect
from wtforms import SelectField
# Import your forms and database models.
from forms import CreateProjectForm, CreateStageForm, RegisterForm, LoginForm, create_filtering_form, SelfFilteringTable, EditUserForm, create_new_record_form, SelectModelForm, CreatePhaseForm, ConceptCatalogSelector
from models import db, Unit, Project, Stage, Phase, Concept, Tool, Job, Machinery, Material, MatGenerator, MoGenerator, MaqGenerator, HerGenerator, Locations, MaterialEntry, MaterialMove, MaterialExit, ToolEntry, ToolMove, ToolExit, Providor, MaqRental, Investor, jobs_history_employees, Employee, JobsHistory, Specialty, NewUser, User, Position, File
import string

COMPANY = 'Vive RAMZSA'
COMPANY_SLOGAN = 'Lujo, sostenibilidad e innovacion, juntos en cada proyecto.'
DATE = date.today()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)

#CONFIGURE LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)

#USER LOGIN CALLBACK
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", 'sqlite:///viveramzsa.db')
db.init_app(app)
with app.app_context():
    db.create_all()
    db.session.commit()


with app.app_context():
    # Check if there are no users in the database
    if not User.query.all():
        # Add the Creator's position
        creator_position = Position(
            name='The Creator',
            description="The creator's position is 'The Creator'."
        )
        db.session.add(creator_position)
        db.session.commit()

        # Retrieve the created position
        created_position = Position.query.filter_by(name='The Creator').first()

        # Add the Creator user
        creator = User(
            email=os.environ.get("CREATOR_USER"),
            password=generate_password_hash(os.environ.get("CREATOR_PASSWORD"), method='pbkdf2:sha256', salt_length=8),
            name='RAZS',
            gram='RAZS',
            is_admin=True,
            position=created_position  # Use the created position
        )
        db.session.add(creator)
        db.session.commit()


# Decorator function to require admin access for a view function.
def login_required(view_func):
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            # Redirect to login page if the user is not logged in
            return redirect(url_for('login'))
        # Call the original view function if the user is logged in and is an admin
        return view_func(*args, **kwargs)
    return decorated_view


def admin_required(view_func):
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            # Redirect to login page if the user is not logged in
            return redirect(url_for('login'))

        # Check if the user is an admin
        user = User.query.get(current_user.get_id())
        if not user.is_admin:
            # Redirect to a forbidden page or show an error message
            return "Forbidden: You must be an admin to access this page."

        # Call the original view function if the user is logged in and is an admin
        return view_func(*args, **kwargs)

    return decorated_view


@app.route("/profile/<int:user_id>")
@login_required
def show_profile(user_id):
    requested_user = User.query.get(user_id) 

    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "profile.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        requested_user=requested_user,
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user,
        route="/profile"
        )


@app.route("/edit_profile/<int:user_id>", methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    user_to_edit = User.query.get(user_id)

    form = EditUserForm(request.form, obj=user_to_edit)

    positions = [(position.id, position.name) for position in Position.query.all()]
    form.position.choices = positions

    if request.method == 'POST':
        if form.validate_on_submit():
            user_to_edit.email = form.email.data
            user_to_edit.name = form.name.data
            user_to_edit.gram = form.gram.data
            user_to_edit.is_admin = bool(form.is_admin.data)
            user_to_edit.about = form.about.data
            user_to_edit.position_id = form.position.data
            
            if form.password.data:
                user_to_edit.password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)

            # Handle image upload
            user_name = user_to_edit.name.replace(' ', '_').lower()
            user_path = os.path.join('static', 'assets', 'users', user_name)
            app.config['USER_PP_UPLOAD_PATH'] = os.path.join(user_path, 'profile_picture')
            app.config['USER_PP_UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.svg', '.webp', '.ico']
            file = request.files['profile_picture']
            if file:
                filename = secure_filename(file.filename)
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['USER_PP_UPLOAD_EXTENSIONS']:
                    abort(400)
                else:
                    filename = secure_filename(f"{user_to_edit.gram.lower()}_pp{file_ext}")
                    file.save(os.path.join(app.config['USER_PP_UPLOAD_PATH'], filename))
                    img_path = os.path.join('..', 'static', 'assets', 'users', user_name, 'profile_picture', filename)
            else:
                img_path = "../static/assets/img/default-profile.jpg"

            user_to_edit.profile_picture = img_path

            db.session.commit()
            return redirect(url_for("show_profile", user_id=user_to_edit.id))
        else:
            print(form.errors)

    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "profile.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        requested_user=user_to_edit,
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user,
        route="/edit_profile",
        form=form
        )






@app.route("/create_new_record", methods=["GET", "POST"])
@login_required
def create_new_record():
    models_list = [Unit, Project, Stage, Phase, Concept, Tool, Job, Machinery, Material, MatGenerator, MoGenerator, MaqGenerator, HerGenerator, Locations, MaterialEntry, MaterialMove, MaterialExit, ToolEntry, ToolMove, ToolExit, Providor, Investor, Employee, JobsHistory, Specialty, Position, File]
    select_form = SelectModelForm()
    select_form.model.choices = [(models_list.index(model), f'{model.__name__}') for model in models_list]
    create_form = None
    model = None

    if request.method == 'POST':
        if 'select' in request.form:
            model_index = int(select_form.model.data)
            session['model_index'] = model_index
            model = models_list[model_index]
            create_form = create_new_record_form(model)
            select_form = None

        elif 'submit' in request.form:
            model_index = session.get('model_index')
            if model_index is not None:
                model = models_list[model_index]
                create_form = create_new_record_form(model)

                new_record_data = f"{model.__name__}("
                for field_name, field in create_form._fields.items():
                    if field_name != 'submit' and field_name != 'csrf_token':
                        # Check if the field is a date field
                        if field.type == 'DateField':
                            # Format the date field correctly
                            field_data = f"date({field.data.year}, {field.data.month}, {field.data.day})"
                        else:
                            if 'project' in f'{model}'.lower() and field_name == 'name':
                                field_data = repr(field.data.title())
                            elif 'img' in field_name.lower():
                                # Handle file upload
                                file = request.files[field_name]
                                if file:
                                    filename = str(eval(f'create_form.{field_name}.data')).lower()
                                    file_ext = os.path.splitext(filename)[1]
                                    if file_ext not in app.config['IMG_UPLOAD_EXTENSIONS']:
                                        abort(400)
                                    else:
                                        file.save(os.path.join(app.config['IMG_UPLOAD_PATH'], filename))
                                        field_data = repr(os.path.join('/static/assets/img', filename))
                            elif 'profile_picture' in field_name.lower():
                                # Handle file upload
                                file = request.files[field_name]
                                if file:
                                    filename = eval(f'create_form.{field_name}.data')
                                    file_ext = os.path.splitext(filename)[1]
                                    if file_ext not in app.config['PP_UPLOAD_EXTENSIONS']:
                                        abort(400)
                                    else:
                                        file.save(os.path.join(app.config['PP_UPLOAD_PATH'], filename))
                                        field_data = repr(os.path.join('/static/assets/profile_pictures', filename))
                            elif 'file_path' in field_name.lower():
                                # Handle file upload
                                file = request.files[field_name]
                                if file:
                                    filename = eval(f'create_form.{field_name}.data')
                                    file_ext = os.path.splitext(filename)[1]
                                    if 'render' in f'{model}'.lower():
                                        if file_ext not in app.config['RENDER_UPLOAD_EXTENSIONS']:
                                            abort(400)
                                        else:
                                            file.save(os.path.join(app.config['RENDER_UPLOAD_PATH'], filename))
                                            field_data = repr(os.path.join('/static/assets/renders', filename))
                                    elif 'plan' in f'{model}'.lower():
                                        if file_ext not in app.config['PLAN_UPLOAD_EXTENSIONS']:
                                            abort(400)
                                        else:
                                            file.save(os.path.join(app.config['PLAN_UPLOAD_PATH'], filename))
                                            field_data = repr(os.path.join('/static/assets/plans', filename))
                                    elif 'diagram' in f'{model}'.lower():
                                        if file_ext not in app.config['DIAGRAM_UPLOAD_EXTENSIONS']:
                                            abort(400)
                                        else:
                                            file.save(os.path.join(app.config['DIAGRAM_UPLOAD_PATH'], filename))
                                            field_data = repr(os.path.join('/static/assets/diagrams', filename))
                                    elif 'video' in f'{model}'.lower():
                                        if file_ext not in app.config['VIDEO_UPLOAD_EXTENSIONS']:
                                            abort(400)
                                        else:
                                            file.save(os.path.join(app.config['VIDEO_UPLOAD_PATH'], filename))
                                            field_data = repr(os.path.join('/static/assets/videos', filename))
                            else:
                                field_data = repr(field.data)

                        new_record_data += f"{field_name}={field_data},"
                
                new_record_data = new_record_data[:-1] + ")"
                new_record = eval(new_record_data)
                db.session.add(new_record)
                db.session.commit()
                flash('New record succesfully created!')
                return redirect(url_for("create_new_record"))
            
    if create_form == None:
        form = select_form
    else:
        form= create_form

    is_admin = False
    if current_user.is_authenticated:
        user = User.query.get(current_user.get_id())
        is_admin = user.is_admin

    return render_template(
        "new_record.html",
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        form=form,
        selected_model = f'{model}'.replace("<class 'models.",'').replace("'>",''),
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user
    )






@app.route('/positions', methods=['GET', 'POST'])
@login_required
def get_positions():
    page_title = 'Positions'

    # Definning the table:
    # Query the SQLAlchemy table
    query_results = db.session.query(Position).all()

    # Convert the query result to a list of dictionaries
    data = []
    for query in query_results:
        query_dict = {
            'id': query.id,
            'name': query.name,
            'description': query.description
        }
        data.append(query_dict)

    # Convert the list of dictionaries to a Pandas DataFrame
    users_table = pd.DataFrame(data)

    self_filtering_table = SelfFilteringTable(
        df=users_table, 
        columns=['id', 'name', 'description'],
        column_types=[int, str, str]
        )
    
    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "tables.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        page_title=page_title, 
        filtering_form=self_filtering_table.form, 
        table=self_filtering_table.table, 
        filters_applied=len(self_filtering_table.filtering_inputs)>0, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, user=current_user, 
        sort_column=self_filtering_table.sort_column, 
        sort_direction=self_filtering_table.sort_direction, 
        columns=self_filtering_table.columns,
        col_span=self_filtering_table.df.shape[1]
        )


@app.route('/users', methods=['GET', 'POST'])
@login_required
def get_users():
    page_title = 'Users'

    # Definning the table:
    # Query the SQLAlchemy table
    users_query = db.session.query(User).all()

    # Convert the query result to a list of dictionaries
    users_data = []
    for user in users_query:
        user_dict = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'position': user.position.name if user.position else None
        }
        users_data.append(user_dict)

    # Convert the list of dictionaries to a Pandas DataFrame
    users_table = pd.DataFrame(users_data)

    self_filtering_table = SelfFilteringTable(
        df=users_table, 
        columns=['id', 'name', 'email', 'position'],
        column_types=[int, str, str, str]
        )
    
    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "users.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        page_title=page_title, 
        filtering_form=self_filtering_table.form, 
        table=self_filtering_table.table, 
        filters_applied=len(self_filtering_table.filtering_inputs)>0, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, user=current_user, 
        sort_column=self_filtering_table.sort_column, 
        sort_direction=self_filtering_table.sort_direction, 
        columns=self_filtering_table.columns,
        col_span=self_filtering_table.df.shape[1]
        )


@app.route('/new_users', methods=['GET', 'POST'])
@login_required
def new_users():
    page_title = 'New Users'
    
    # Definning the table:
    # Query the SQLAlchemy table
    users_query = db.session.query(NewUser).all()

    # Convert the query result to a list of dictionaries
    users_data = []
    for user in users_query:
        user_dict = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'status': user.status
        }
        users_data.append(user_dict)

    # Convert the list of dictionaries to a Pandas DataFrame
    users_table = pd.DataFrame(users_data)

    self_filtering_table = SelfFilteringTable(
        df=users_table, 
        columns=['id', 'name', 'email', 'status'],
        column_types=[int, str, str, str]
        )

    positions = Position.query.all()

    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "new_users.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        page_title=page_title, 
        filtering_form=self_filtering_table.form, 
        table=self_filtering_table.table, 
        filters_applied=len(self_filtering_table.filtering_inputs)>0, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, user=current_user, 
        sort_column=self_filtering_table.sort_column, 
        sort_direction=self_filtering_table.sort_direction, 
        columns=self_filtering_table.columns,
        positions = positions,
        col_span=self_filtering_table.df.shape[1] + 3
        )


@app.route("/create_new_user/<int:new_user_id>", methods=['POST'])
@admin_required  # Require admin access in addition to login
def create_new_user(new_user_id):
    new_user = db.get_or_404(NewUser, new_user_id)
    
    # Check the value of 'approval_status' in the form data
    approval_status = request.form.get('approval_status')
    if approval_status == 'Approved':
        new_user.status = 'Approved'

        # Define the path for the new user directory
        user_name = new_user.name.replace(' ', '_').lower()
        new_user_path = os.path.join('static', 'assets', 'users', user_name)
            
        try:
            # Create the main user directory
            os.makedirs(new_user_path, exist_ok=True)
            
            # Create subdirectories inside the main user directory
            os.makedirs(os.path.join(new_user_path, 'profile_picture'), exist_ok=True)
            
        except OSError as e:
            flash(f'Error creating user directories: {e}', 'danger')
            return redirect(url_for("new_user"))

        # Check if the 'is_admin' checkbox is checked
        is_admin = request.form.get("is_admin") == 'True'
        position_id = int(request.form.get("position"))
        position = Position.query.get(position_id)

        user_to_add = User(
            email=new_user.email,
            password=new_user.password,
            name=new_user.name,
            gram=''.join(word[0].capitalize() for word in new_user.name.split()),
            is_admin=is_admin,
            position=position
        )
        db.session.add(user_to_add)
        db.session.commit()

    elif approval_status == 'Denied':
        new_user.status = 'Denied'
        db.session.commit()
    
    return redirect(url_for('new_users'))


@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        new_user = NewUser.query.filter_by(email=form.email.data).first()
        if user:
            flash("You've already signed PU with that email, <a href='" + url_for('login') + "'>log in</a> instead!")
        elif new_user:
            flash("Your account has already been registered but it has not been aproved yet. You will be notified when it does.")
        else:
            hash_and_salted_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
            new_user = NewUser(
                email = form.email.data,
                password = hash_and_salted_password,
                name = form.name.data
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('get_all_projects'))
        
    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "register.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        form=form, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user
        )


@app.route('/login', methods = ['POST', 'GET'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        new_user = NewUser.query.filter_by(email=form.email.data).first()
        if user:
            # Check stored password hash against entered password hashed.
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('get_all_projects'))
            else:
                flash('Password incorrect, please try again.')
        elif new_user:
            flash("Your account has not been aproved yet. You will be notified when it does.")
        else:
            flash('That email does not exist, please <a href="' + url_for('register') + '">register</a> or try again.')

    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "login.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        form=form, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user
        )


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_projects'))


@app.route('/')
def get_all_projects():
    projects = Project.query.all()

    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "index.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        all_projects=projects, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user)



# List of subdirectories to be created within each project and stage directory
SUBDIRECTORIES = [
    'img',
    'renders',
    'plans',
    'diagramas',
    'invoices',
    'notes',
    'payroll',
    'licencies_and_permits',
    'laboratory_results',
    'contracts',
    'advances'
]

# PROJECTS MANAGEMENT
@app.route("/project/<project_name>", methods=['GET', 'POST'])
def show_project(project_name):
    requested_project = Project.query.filter_by(name=project_name.replace('_', ' ').title()).first()
    #requested_project = Project.query.get(project_id)
    stages = Stage.query.filter_by(project_id=requested_project.id).all()

    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "project.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        project=requested_project, 
        stages=stages, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user
        )



@app.route("/new_project", methods=["GET", "POST"])
@admin_required  # Require admin access in addition to login
def add_new_project():
    form = CreateProjectForm()
    if form.validate_on_submit():

        project_db_name = Project.query.filter_by(name=form.name.data.title()).first()

        if project_db_name:
            flash('That project name already exists, please choose a new one.')
        else:
            # Define the path for the new project directory
            project_name = form.name.data.replace(' ', '_').lower()
            new_project_path = os.path.join('static', 'assets', 'projects', project_name)
            
            try:
                # Create the main project directory
                os.makedirs(new_project_path, exist_ok=True)
            
                # Create subdirectories inside the main project directory
                for subdirectory in SUBDIRECTORIES:
                    os.makedirs(os.path.join(new_project_path, subdirectory), exist_ok=True)

                os.makedirs(os.path.join(new_project_path, 'stages'), exist_ok=True)

            except OSError as e:
                flash(f'Error creating project directories: {e}', 'danger')
                return redirect(url_for("add_new_project"))
            
            # Handle image upload
            app.config['PROJECT_IMG_UPLOAD_PATH'] = os.path.join(new_project_path, 'img')
            app.config['PROJECT_IMG_UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.svg', '.webp', '.ico']
            file = request.files['img']
            if file:
                filename = secure_filename(file.filename)
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['PROJECT_IMG_UPLOAD_EXTENSIONS']:
                    abort(400)
                else:
                    filename = secure_filename(f"main_project_image{file_ext}")
                    file.save(os.path.join(app.config['PROJECT_IMG_UPLOAD_PATH'], filename))
                    img_path = os.path.join('/static', 'assets', 'projects', project_name, 'img', filename)
            else:
                img_path = "/static/assets/img/I.1.png"
            
            # Create the new project record in the database
            new_project = Project(
                name=form.name.data.title(),
                slogan=form.slogan.data,
                description=form.description.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                img=img_path
            )
            db.session.add(new_project)
            db.session.commit()
            
            return redirect(url_for("get_all_projects"))
    
    is_admin = False
    if current_user.is_authenticated:
        user = User.query.get(current_user.get_id())
        is_admin = user.is_admin
    
    return render_template(
        "new_project.html",
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        form=form, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user
    )


@app.route("/edit_project/<int:project_id>", methods=["GET", "POST"])
@admin_required  # Require admin access in addition to login
def edit_project(project_id):
    project_to_edit = db.get_or_404(Project, project_id)
    form = CreateProjectForm(obj=project_to_edit)
    form.submit.label.text = "Edit Project"
    if form.validate_on_submit():

        project_db_name = Project.query.filter(Project.name == form.name.data.title(), Project.id != project_id).first()

        if project_db_name:
            flash('That project name already exists, please choose a new one.')
        else:
            try:
                project_name =  project_to_edit.name.replace(' ', '_').lower()
                project_path = os.path.join('static', 'assets', 'projects', project_name)

                # Move the project directory if the name has changed
                if project_to_edit.name != form.name.data:
                    old_project_path = project_path
                    # Define the path for the project directory
                    project_name = form.name.data.replace(' ', '_').lower()
                    project_path = os.path.join('static', 'assets', 'projects', project_name)

                    os.rename(old_project_path, project_path)
                

                # Handle image upload
                app.config['PROJECT_IMG_UPLOAD_PATH'] = os.path.join(project_path, 'img')
                app.config['PROJECT_IMG_UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.svg', '.webp', '.ico']
                file = request.files['img']
                if file:
                    filename = secure_filename(file.filename)
                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in app.config['PROJECT_IMG_UPLOAD_EXTENSIONS']:
                        abort(400)
                    else:
                        filename = secure_filename(f"main_project_image{file_ext}")
                        file.save(os.path.join(app.config['PROJECT_IMG_UPLOAD_PATH'], filename))
                        img_path = os.path.join('/static', 'assets', 'projects', project_name, 'img', filename)
                else:
                    img_path = os.path.join(project_path, 'img', project_to_edit.img.split('/')[-1])
                    print(img_path)
                
                # Update the project record in the database
                project_to_edit.name = form.name.data.title()
                project_to_edit.slogan = form.slogan.data
                project_to_edit.description = form.description.data
                project_to_edit.start_date = form.start_date.data
                project_to_edit.end_date = form.end_date.data
                project_to_edit.img = img_path
                
                db.session.commit()
                
                return redirect(url_for('show_project', project_name=project_to_edit.name.lower().replace(' ', '_')))
            
            except OSError as e:
                flash(f'Error editing project: {e}', 'danger')
    
    is_admin = False
    if current_user.is_authenticated:
        user = User.query.get(current_user.get_id())
        is_admin = user.is_admin
    
    return render_template(
        "new_project.html",
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        form=form, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user,
        is_edit=True,
        project = project_to_edit
    )


@app.route("/delete/<int:project_id>")
@admin_required  # Require admin access in addition to login
def delete_project(project_id):
    project_to_delete = db.get_or_404(Project, project_id)

    #Locate and delete all the project's stages.
    stages = Stage.query.filter_by(project_id=project_id).all()
    for stage in stages:
        delete_stage(stage.id)

    # Delete the file associated with the project if it exists
    project_name = project_to_delete.name.replace(' ', '_').lower()
    dir_path = os.path.join('static', 'assets', 'projects', project_name)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    
    db.session.delete(project_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_projects'))




# STAGES MANAGEMENT
@app.route("/project/<project_name>/stage/<stage_name>", methods=['GET', 'POST'])
def show_stage(project_name, stage_name):
    project_name_title = project_name.replace('_', ' ').title()
    stage_name_title = stage_name.replace('_', ' ').title()
    
    # Query the project and the stage
    requested_project = Project.query.filter_by(name=project_name_title).first()
    requested_stage = Stage.query.filter_by(project_id=requested_project.id, name=stage_name_title).first()
    
    if not requested_project or not requested_stage:
        abort(404)
    
    phases = Phase.query.filter_by(stage_id=requested_stage.id).all()
    
    # Convert the phases to a list of dictionaries
    data = []
    for phase in phases:
        phase_dict = {
            'id': phase.id,
            'code': phase.code,
            'name': phase.name,
            'description': phase.description
        }
        data.append(phase_dict)
    
    # Convert the list of dictionaries to a Pandas DataFrame
    phases_table = pd.DataFrame(data)
    
    self_filtering_table = SelfFilteringTable(
        df=phases_table, 
        columns=['id', 'code', 'name', 'description'],
        column_types=[int, str, str, str]
    )
    
    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "stage.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        project=requested_project, 
        stage=requested_stage, 
        filtering_form=self_filtering_table.form,
        table=self_filtering_table.table, 
        filters_applied=len(self_filtering_table.filtering_inputs) > 0, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user, 
        sort_column=self_filtering_table.sort_column, 
        sort_direction=self_filtering_table.sort_direction, 
        columns=self_filtering_table.columns,
        col_span=self_filtering_table.df.shape[1]
    )



@app.route("/new_stage/<int:project_id>", methods=["GET", "POST"])
@admin_required  # Require admin access in addition to login
def add_new_stage(project_id):
    form = CreateStageForm()
    project = db.get_or_404(Project, project_id)
    
    if form.validate_on_submit():

        stage_db_name = Stage.query.filter_by(name=form.name.data.title(), project_id=project_id).first()

        if stage_db_name:
            flash('That stage name already exists in this project, please choose a new one.')
        else:
            # Define the path for the new stage directory
            stage_name = form.name.data.replace(' ', '_').lower()
            project_name = project.name.replace(' ', '_').lower()
            new_stage_path = os.path.join('static', 'assets', 'projects', project_name, 'stages', stage_name)
            
            try:
                # Create the main stage directory
                os.makedirs(new_stage_path, exist_ok=True)
            
                # Create subdirectories inside the main stage directory
                for subdirectory in SUBDIRECTORIES:
                    os.makedirs(os.path.join(new_stage_path, subdirectory), exist_ok=True)
            
            except OSError as e:
                flash(f'Error creating stage directories: {e}', 'danger')
                return redirect(url_for("add_new_stage", project_id=project_id))
            
            # Handle image upload
            app.config['STAGE_IMG_UPLOAD_PATH'] = os.path.join(new_stage_path, 'img')
            app.config['STAGE_IMG_UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.svg', '.webp', '.ico']
            file = request.files['img']
            if file:
                filename = secure_filename(file.filename)
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['STAGE_IMG_UPLOAD_EXTENSIONS']:
                    abort(400)
                else:
                    filename = secure_filename(f"main_stage_image{file_ext}")
                    file.save(os.path.join(app.config['STAGE_IMG_UPLOAD_PATH'], filename))
                    img_path = os.path.join('/static', 'assets', 'projects', project_name, 'stages', stage_name, 'img', filename)
            else:
                img_path = "/static/assets/img/I.1.png"
            
            # Create the new stage record in the database
            new_stage = Stage(
                name=form.name.data.title(),
                slogan=form.slogan.data,
                description=form.description.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                img=img_path,
                project_id=project_id
            )
            db.session.add(new_stage)
            db.session.commit()
            
            return redirect(url_for("show_project", project_name=project_name))
    
    is_admin = False
    if current_user.is_authenticated:
        user = User.query.get(current_user.get_id())
        is_admin = user.is_admin
    
    return render_template(
        "new_stage.html",
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        form=form, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user,
        project=project
    )



@app.route("/edit_stage/<int:stage_id>", methods=["GET", "POST"])
@admin_required  # Require admin access in addition to login
def edit_stage(stage_id):
    stage_to_edit = db.get_or_404(Stage, stage_id)
    project = db.get_or_404(Project, stage_to_edit.project_id)
    form = CreateStageForm(obj=stage_to_edit)
    form.submit.label.text = "Edit Stage"
    if form.validate_on_submit():

        stage_db_name = Stage.query.filter(Stage.name == form.name.data.title(), Stage.id != stage_id, Stage.project_id == stage_to_edit.project_id).first()

        if stage_db_name:
            flash('That stage name already exists in this project, please choose a new one.')
        else:
            try:
                project_name = project.name.replace(' ', '_').lower()
                stage_name = stage_to_edit.name.replace(' ', '_').lower()
                stage_path = os.path.join('static', 'assets', 'projects', project_name, 'stages', stage_name)

                # Move the stage directory if the name has changed
                if stage_to_edit.name != form.name.data:
                    old_stage_path = stage_path
                    # Define the path for the stage directory
                    stage_name = form.name.data.replace(' ', '_').lower()
                    stage_path = os.path.join('static', 'assets', 'projects', project_name, 'stages', stage_name)

                    os.rename(old_stage_path, stage_path)
                

                # Handle image upload
                app.config['STAGE_IMG_UPLOAD_PATH'] = os.path.join(stage_path, 'img')
                app.config['STAGE_IMG_UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.svg', '.webp', '.ico']
                file = request.files['img']
                if file:
                    filename = secure_filename(file.filename)
                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in app.config['STAGE_IMG_UPLOAD_EXTENSIONS']:
                        abort(400)
                    else:
                        filename = secure_filename(f"main_stage_image{file_ext}")
                        file.save(os.path.join(app.config['STAGE_IMG_UPLOAD_PATH'], filename))
                        img_path = os.path.join('/static', 'assets', 'projects', project_name, 'stages', stage_name, 'img', filename)
                else:
                    img_path = os.path.join(stage_path, 'img', stage_to_edit.img.split('/')[-1])
                
                # Update the stage record in the database
                stage_to_edit.name = form.name.data.title()
                stage_to_edit.slogan=form.slogan.data
                stage_to_edit.description=form.description.data
                stage_to_edit.start_date = form.start_date.data
                stage_to_edit.end_date = form.end_date.data
                stage_to_edit.img = img_path
                
                db.session.commit()
                
                return redirect(url_for('show_stage', project_name=project_name, stage_name=stage_name))
            
            except OSError as e:
                flash(f'Error editing stage: {e}', 'danger')
    
    is_admin = False
    if current_user.is_authenticated:
        user = User.query.get(current_user.get_id())
        is_admin = user.is_admin
    
    return render_template(
        "new_stage.html",
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        form=form, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user,
        is_edit=True,
        stage=stage_to_edit
    )



@app.route("/delete_stage/<int:stage_id>")
@admin_required  # Require admin access in addition to login
def delete_stage(stage_id):
    stage_to_delete = db.get_or_404(Stage, stage_id)
    project = db.get_or_404(Project, stage_to_delete.project_id)
    
    # Delete the directory associated with the stage if it exists
    stage_name = stage_to_delete.name.replace(' ', '_').lower()
    project_name = project.name.replace(' ', '_').lower()
    dir_path = os.path.join('static', 'assets', 'projects', project_name, 'stages', stage_name)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    
    db.session.delete(stage_to_delete)
    db.session.commit()
    return redirect(url_for('show_project', project_name=project_name))



# PHASES MANAGEMENT
@app.route("/new_phase/<int:stage_id>", methods=["GET", "POST"])
@admin_required  # Require admin access in addition to login
def add_new_phase(stage_id):
    form = CreatePhaseForm()
    stage = db.get_or_404(Stage, stage_id)
    project = db.get_or_404(Project, stage.project_id)
    
    if form.validate_on_submit():

        phase_db_name = Phase.query.filter_by(name=form.name.data.title(), stage_id=stage_id).first()

        if phase_db_name:
            flash('That phase name already exists in this stage, please choose a new one.')
        else:
            # Generate the phase code
            existing_phases = Phase.query.filter_by(stage_id=stage_id).all()
            position = len(existing_phases)
            phase_code = string.ascii_uppercase[position]

            # Create the new phase record in the database
            new_phase = Phase(
                name=form.name.data.title(),
                description=form.description.data,
                code=phase_code,
                stage_id=stage_id
            )

            db.session.add(new_phase)
            db.session.commit()
            
            return redirect(url_for("show_stage", project_name=project.name.lower().replace(' ', '_'), stage_name=stage.name.lower().replace(' ', '_')))
    
    is_admin = False
    if current_user.is_authenticated:
        user = User.query.get(current_user.get_id())
        is_admin = user.is_admin
    
    return render_template(
        "new_phase.html",
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        form=form, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user,
        project=project
    )



@app.route("/edit_phase/<int:phase_id>", methods=["GET", "POST"])
@admin_required  # Require admin access in addition to login
def edit_phase(phase_id):
    phase_to_edit = db.get_or_404(Phase, phase_id)
    stage = db.get_or_404(Stage, phase_to_edit.stage_id)
    project = db.get_or_404(Project, stage.project_id)
    form = CreatePhaseForm(obj=phase_to_edit)
    form.submit.label.text = "Edit Phase"
    
    if form.validate_on_submit():

        phase_db_name = Phase.query.filter(Phase.name == form.name.data.title(), Phase.id != phase_id, Phase.stage_id == phase_to_edit.stage_id).first()

        if phase_db_name:
            flash('That phase name already exists in this stage, please choose a new one.')
        else:
            try:
                # Update the stage record in the database
                phase_to_edit.name = form.name.data.title()
                phase_to_edit.description=form.description.data
                
                db.session.commit()
                
                return redirect(url_for('show_stage', project_name=project.name, stage_name=stage.name))
            
            except OSError as e:
                flash(f'Error editing stage: {e}', 'danger')
    
    is_admin = False
    if current_user.is_authenticated:
        user = User.query.get(current_user.get_id())
        is_admin = user.is_admin
    
    return render_template(
        "new_phase.html",
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        form=form, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user,
        project=project,
        phase=phase_to_edit,
        is_edit=True
    )



# CONCEPTS MANAGEMENT
@app.route("/project/<project_name>/stage/<stage_name>/concepts_catalog", methods=["GET", "POST"])
@admin_required  # Require admin access in addition to login
def show_concepts(project_name, stage_name):
    
    project_name_title = project_name.replace('_', ' ').title()
    stage_name_title = stage_name.replace('_', ' ').title()

    page_title = f"Concepts Catalog of stage {stage_name_title} of project {project_name_title}" 
    
    # Query the project and the stage
    requested_project = Project.query.filter_by(name=project_name_title).first()
    requested_stage = Stage.query.filter_by(project_id=requested_project.id, name=stage_name_title).first()

    phases = Phase.query.filter_by(stage_id=requested_stage.id).all()

    data = []
    for phase in phases:
        concepts = Concept.query.filter_by(phase_id=phase.id).all()
        for concept in concepts:

            concept_mat_import = 0
            mat_gens = MatGenerator.query.filter_by(concept_id=concept.id).all()
            for mat_gen in mat_gens:
                material = Material.query.filter_by(id=mat_gen.material_id).first()
                amount = mat_gen.quantity * material.price
                concept_mat_import = concept_mat_import + amount

            concept_maq_import = 0
            maq_gens = MaqGenerator.query.filter_by(concept_id=concept.id).all()
            for maq_gen in maq_gens:
                machinery = Machinery.query.filter_by(id=maq_gen.machinery_id).first()
                amount = maq_gen.quantity * machinery.price
                concept_maq_import = concept_maq_import + amount

            concept_mo_import = 0
            mo_gens = MoGenerator.query.filter_by(concept_id=concept.id).all()
            for mo_gen in mo_gens:
                job = Job.query.filter_by(id=mo_gen.job_id).first()
                amount = mo_gen.quantity * job.price
                concept_mo_import = concept_mo_import + amount

            concept_her_import = 0.03 * concept_mo_import

            direct_cost = concept_her_import + concept_maq_import + concept_mat_import + concept_mo_import


            concepts_dict = {
                'phase': phase.code,
                'code': concept.code,
                'name': concept.name,
                'quantity': concept.quantity,
                'unit': concept.unit,
                'material unit price': concept_mat_import/concept.quantity,
                'material total': concept_mat_import,
                'machinery unit price': concept_mat_import/concept.quantity,
                'machinery total': concept_mat_import,
                'labour unit price': concept_mat_import/concept.quantity,
                'labour total': concept_mat_import,
                'tools unit price': concept_mat_import/concept.quantity,
                'tools total': concept_mat_import,
                'unit price': direct_cost/concept.quantity,
                'direct cost': direct_cost,
            }
            data.append(concepts_dict)
    
    
    # Convert the list of dictionaries to a Pandas DataFrame
    concepts_table = pd.DataFrame(data)
    
    self_filtering_table = SelfFilteringTable(
        df=concepts_table, 
        columns=concepts_table.columns.tolist(),
        column_types=[str, str, str, float, str, float, float, float, float, float, float, float, float, float, float]
    )
    
    is_admin = False
    if current_user.is_authenticated:
        # Get the user from the database using the user ID stored in current_user
        user = User.query.get(current_user.get_id())
        # Check if the user is an admin
        is_admin = user.is_admin

    return render_template(
        "concepts_catalog.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        page_title=page_title, 
        project=requested_project, 
        stage=requested_stage, 
        filtering_form=self_filtering_table.form,
        table=self_filtering_table.table, 
        filters_applied=len(self_filtering_table.filtering_inputs) > 0, 
        logged_in=current_user.is_authenticated, 
        is_admin=is_admin, 
        user=current_user, 
        sort_column=self_filtering_table.sort_column, 
        sort_direction=self_filtering_table.sort_direction, 
        columns=self_filtering_table.columns,
        col_span=self_filtering_table.df.shape[1]
    )



# GENERAL PAGES
@app.route("/about")
def about():
    return render_template(
        "about.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        logged_in=current_user.is_authenticated, 
        user=current_user)


@app.route("/contact")
def contact():
    return render_template(
        "contact.html", 
        company=COMPANY, 
        slogan=COMPANY_SLOGAN, 
        date=DATE, 
        logged_in=current_user.is_authenticated, 
        user=current_user)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
