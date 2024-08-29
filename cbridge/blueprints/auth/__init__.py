from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user

from cbridge.models.user import User
from cbridge.extensions import db, bcrypt

from .forms import *

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username == form.username.data).first()
        if (user):
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                if len(user.get_roles()) == 1:
                    session['current_role'] = user.get_roles()[0]
                else:
                    return redirect(url_for('auth.selectrole'))

                return redirect(url_for('profile.index'))
        flash('Invalid credentials')

    return render_template('login.html', form=form)

@auth_bp.route('/role', methods=['GET', 'POST'])
@login_required
def selectrole():
    form = RoleSwitchForm()
    roles = current_user.get_roles()
    form.role.choices = [(role, role.capitalize()) for role in roles]

    if form.validate_on_submit():
        selected_role = form.role.data

        # Cross-check the selected role with available roles
        if selected_role in roles:
            session['current_role'] = selected_role
            flash(f'Role {selected_role} applied successfully!', 'success')
            return redirect(url_for('home.index'))
        else:
            flash('Invalid role selection!', 'danger')

    return render_template('role_switch.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    print(request.method)
    
    if form.validate_on_submit():
        print('yoo')
        def verified_password(): return (form.password.data == form.confirm_password.data)

        if verified_password():
            print('Registering')
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            new_user = User(
                username = form.username.data,
                password = hashed_password,
                name = form.name.data,
                date_birth = form.date_birth.data,
                identification = form.identification.data,
                telephone = form.telephone.data,
                email = form.email.data,
                address = form.address.data
                )
            
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully!')
            return redirect(url_for('auth.login'))
        else:
            print('Pass')
            flash('Password mismatch')
    else:
        print('Validation failed')
    print ('sending')
    return render_template('register.html', form=form)
