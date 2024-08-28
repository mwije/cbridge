from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from cbridge.decorators import role_required
from cbridge.models.user import *
from cbridge.extensions import db, bcrypt

book_bp = Blueprint('book', __name__)

@book_bp.route('/schedule')
@role_required('clinician')
def clinicianschedule():
    title = "Clinician's Schedule"
    bookings = []
    book = {'date' : '2022-2-2', 'clinic' : 'ucfm'}
    bookings.append(book)
    return render_template('schedule.html', title = title, bookings=bookings)

@book_bp.route('/book')
@role_required('client', 'helper')
def booking():
    title = "My Booking"
    bookings = {}
    return render_template('schedule.html', title = title, bookings=bookings)


def get_bookings(clinician):
    return current_user.clinicians.id