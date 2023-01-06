# -*- coding: utf-8 -*-

from flask_login import logout_user, login_required, current_user
from flask_babel import gettext
from flask import render_template, redirect, url_for, request, flash, session
from pyotp import random_base32

from linufy.libs import configurations, users, organizations, roles, validator
from linufy.libs.roles import require_permission
from linufy.libs.breadcrumb import breadcrumb

from .routes import admin


@admin.route('/signup/<organization_id>/<email>')
def signup_organization(organization_id, email):
    return render_template('signup.html', organization_id=organization_id, email=email)

@admin.route('/signup')
def signup():
    if configurations.get('users_can_register').value == "False":
        flash('Registrations are disabled. Please contact the administrator.', 'warning')
        return redirect(url_for('admin.login'))
    return render_template('signup.html')


@admin.route('/signup', methods=['POST'])
def signup_post():
    warning = False
    if not request.form.get('name'):
        flash(gettext('Please enter your name to register.'), 'warning')
        warning = True
    if not request.form.get('email'):
        flash(gettext('Please enter an email address to register.'), 'warning')
        warning = True
    if not validator.email( request.form.get('email') ):
        flash(gettext('Please enter a valid email address to register.'), 'warning')
        warning = True
    if not request.form.get('password'):
        flash(gettext('Please enter a password to register.'), 'warning')
        warning = True
    if request.form.get('password') != request.form.get('repeat_password'):
        flash(gettext('Your passwords must match to register.'), 'warning')
        warning = True
    if not request.form.get('terms'):
        flash(gettext('Please accept the terms of use to register.'), 'warning')
        warning = True
    if not request.form.get('organization') and not request.form.get('organization_id'):
        flash(gettext('Please enter a valid organization name to register.'), 'warning')
        warning = True

    if not request.form.get('organization'):
        organization_id = request.form.get('organization_id')
    else:
        organization = request.form.get('organization')
        new_organization = organizations.add(organization, 'customer')
        if new_organization:
            organization_id = new_organization.id
        else:
            flash(gettext('An error occurred while creating your organization.'), 'warning')
            warning = True

    if warning == True:
        organization_id = request.form.get('organization_id')
        if organization_id:
            email = request.form.get('email')
            return redirect(url_for('admin.signup_organization', organization_id=organization_id, email=email))
        return redirect(url_for('admin.signup'))

    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    for role in roles.get_all(organization_id):
        if role.by_default == True:
            break

    if users.add(name, email, password, organization_id, role.id):
        return redirect(url_for('admin.login'))
    else:
        if organization_id:
            return redirect(url_for('admin.signup_organization', organization_id=organization_id, email=email))
        return redirect(url_for('admin.signup'))


@admin.route('/signup/confirmation/<user_id>/<registration_key>')
def signup_confirmation(user_id, registration_key):
    user_meta = users.get_meta(user_id)
    if user_meta['registration_confirmed'] == 'False':
        if user_meta['registration_key'] == registration_key:
            users.edit_meta(user_id, 'registration_confirmed', 'True')
            flash(gettext('Your email address has been successfully validated. You can now sign in.'), 'success')
        else:
            flash(gettext('Your validation code is invalid. Try again.'), 'warning')
    else:
        flash(gettext('Your email address is already validated.'), 'warning')
    return redirect(url_for('admin.login'))


@admin.route('/forgot')
def forgot_password():
    return render_template('forgot-password.html')


@admin.route('/forgot', methods=['POST'])
def forgot_password_post():
    email = request.form.get('email')
    users.request_new_password(email)
    return redirect(url_for('admin.login'))


@admin.route('/forgot/reset/<user_id>/<forgot_password_key>')
def forgot_password_reset(user_id, forgot_password_key):
    if users.get(user_id):
        if 'forgot_password_key' in users.get_meta(user_id) and users.get_meta(user_id)['forgot_password_key'] == forgot_password_key:
            return render_template('reset-password.html')
    return redirect(url_for('admin.login'))    


@admin.route('/forgot/reset/<user_id>/<forgot_password_key>', methods=['POST'])
def forgot_password_reset_post(user_id, forgot_password_key):
    if users.get(user_id):
        if users.get_meta(user_id)['forgot_password_key'] == forgot_password_key:
            password = request.form.get('password')
            repeat_password = request.form.get('repeat_password')
            if password == repeat_password:
                users.set_new_password(user_id, password)
            else:
                flash(gettext('The passwords are not identical. Please try again.'), 'warning')
                return redirect(url_for('admin.forgot_password_reset', user_id=user_id, forgot_password_key=forgot_password_key))
    return redirect(url_for('admin.login')) 


@admin.route('/login')
def login(email=None):
    next = request.args.get('next') if request.args.get('next') else None
    return render_template('login.html', next=next, email=email)


@admin.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    next = request.form.get('next') if request.form.get('next') else None
    return users.signin(email, password, remember, next)


@admin.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('admin.login'))


@admin.route('/users/edit/<user_id>')
@admin.route('/profile')
@login_required
@require_permission('users.edit')
def profile(user_id=None):
    if user_id is None:
        user_id = current_user.id
    user = users.get(user_id)
    if user.mfa_hash:
        return render_template('profile.html', title_page="Profile", user=user)
    else:
        mfa_hash = random_base32()
        qrcode_data = "otpauth://totp/{}:{}?secret={}&issuer={}".format(
            configurations.get('sitename').value, user.email, mfa_hash, configurations.get('sitename').value)
        return render_template('profile.html', title_page="Profile", mfa_hash=mfa_hash,
                               qrcode_data=qrcode_data, user=user, keys=users.get_key(user_id))


@admin.route('/users/edit/<user_id>', methods=['POST'])
@admin.route('/profile', methods=['POST'])
@login_required
@require_permission('users.edit')
def profile_post(user_id=None):
    if user_id is None:
        users.edit(current_user.id)
        return redirect(url_for('admin.profile'))
    users.edit(user_id)
    return redirect(url_for('admin.profile', user_id=user_id))


@admin.route('/users')
@login_required
@breadcrumb('Users', root=True)
@require_permission('users.list')
def users_list():
    return render_template('users.html', title_page="Users", users=users.get_all())


@admin.route('/users/delete/<user_id>')
@login_required
@require_permission('users.edit')
def users_delete(user_id):
    users.delete(user_id)
    return redirect(url_for('admin.users_list'))


@admin.route('/users/<user_id>/key/delete/<key_id>')
@login_required
@require_permission('users.edit')
def users_api_key_delete(user_id, key_id):
    users.delete_key(user_id, key_id)
    return redirect(url_for('admin.profile', user_id=user_id))
