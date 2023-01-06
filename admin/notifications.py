# -*- coding: utf-8 -*-

from flask_login import login_required
from flask import redirect, url_for, request

from linufy.libs import notifications

from .routes import admin

@admin.route('/notifications/<notification_id>')
@login_required
def redirect_notification(notification_id):
    notification = notifications.get(notification_id)
    if notification == None:
        return redirect(url_for('admin.index'))
    else:
        if notification.object_type == 'user':
            notifications.delete(notification_id)
            return redirect(url_for('admin.users_list'))
        if notification.object_type == 'comment':
            notifications.delete(notification_id)
            return redirect(url_for('admin.comments_list'))
    notifications.delete(notification_id)
    return redirect(url_for('admin.index'))