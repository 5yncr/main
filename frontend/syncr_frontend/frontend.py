import platform
import subprocess
from os import path

from flask import Flask
from flask import render_template
from flask import request

app = Flask(__name__)  # create the application instance
app.config.from_object(__name__)  # load config from this file , frontend.py

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='development key',
    TEMPLATES_AUTO_RELOAD=True,
))
app.config.from_envvar('SYNCR_SETTINGS', silent=True)

# Backend Access Functions


def open_file_location(file_path):
    # Placeholder until backend communication is set-up
    file_path = path.dirname(path.abspath(__file__))

    op_sys = platform.system()
    if op_sys == 'Windows':
        subprocess.Popen(['explorer', file_path])
    if op_sys == 'Linux':
        subprocess.Popen(['xdg-open', file_path])
    if op_sys == 'Darwin':
        subprocess.Popen(['open', file_path])


def remove_file(file_path):
    # Remove file at specified location from drop info
    return


def get_owned_drops():
    # Placeholder until backend communication is set-up
    # TODO: validate data structure
    return [{'name': 'O_Drop_1'}, {'name': 'O_Drop_2'}]


def get_subscribed_drops():
    # Placeholder until backend communication is set-up
    # TODO: validate data structure
    return [{'name': 'S_Drop_1'}, {'name': 'S_Drop_2'}, {'name': 'S_Drop_3'}]


def get_selected_drop(drop_id):
    # Placeholder until backend communication is set-up
    # TODO: validate data structure

    # if drop does not exist -> return default drop display

    return {
        'name': drop_id, 'files': [
            {'name': 'FileOne', 'type': 'text', 'occr': 'once'},
            {'name': 'FileTwo', 'type': 'image', 'occr': 'many'},
            {'name': 'FileThree', 'type': 'video', 'occr': 'once'},
            {'name': 'FileFour', 'type': 'text', 'occr': 'once'},
            {'name': 'Folder', 'type': 'folder', 'occr': 'many'},
        ], 'permission': get_permission(drop_id),
    }


def get_conflicting_files(drop_id):
    # eventually will be used to retrieve files of conflicting drops
    pass


def get_permission(drop_id):
    # returns the permission type of the drop ID
    owned_drops = get_owned_drops()

    for drop in owned_drops:
        if drop['name'] == drop_id:
            return "owned"

    return "subscribed"


def decline_conflict_file(file_path):
    # if a file is in conflict with master
    # declining changes leaves file on master the same
    # backend communication: remove conflict file
    return


def accept_conflict_file(file_path):
    # if a file is in conflict with file in master
    # accepting changes modifies master file
    # backend communication: change master file
    return


def accept_changes(file_path):
    # Accepts the proposed changes of a file
    # backend: modify the master file with proposed changes
    return


def decline_changes(file_path):
    # Declines the proposed changes of a file
    # backend: discard changes, keep master file
    return


@app.route('/view_conflicts/<drop_id>')
def view_conflicts(drop_id):
    # if no drop is selected
        # do nothing
    # else
        # retrieve files from all conflicting drops
        # display said files in body of page
    return show_drops(drop_id, "Current conflicts")


@app.route('/add_file/<drop_id>')
def add_file(drop_id):
    # if no drop is selected
        # do nothing
    # else
        # communicate change to backend.
        # open finder / windows equivalent to choose file.
    return show_drops(drop_id, "file added")


@app.route('/share_drop/<drop_id>')
def share_drop(drop_id):
    # if no drop is selected
        # do nothing
    # else
        # communicate with backend to retrieve public key
        # display public key in the body of the page
    return show_drops(drop_id, "drop shared")


@app.route('/view_pending_changes/<drop_id>')
def view_pending_changes(drop_id):
    # if no drop is selected
        # do nothing
    # else
        # display pending file changes on body of page
        # should provide options to review/accept pending changes
    return show_drops(drop_id, "view pending changes")


@app.route('/view_owners/<drop_id>')
def view_owners(drop_id):
    # if no drop is selected
        # do nothing
    # else
        # communicate with backend to retrieve owners
        # display owners on body of page
        # give user option to remove owners if primary owner
    return show_drops(drop_id, "list of owners")


@app.route('/whitelist/<drop_id>')
def whitelist(drop_id):
    # if no drop is selected
        # do nothing
    # else
        # display prompt on page to whitelist node
        # prompt should communicate with backend
    return show_drops(drop_id, "node whitelisted")


@app.route('/delete_drop/<drop_id>')
def delete_drop(drop_id):
    # if no drop is selected
        # do nothing
    # else
        # communicate deletion to backend.
        # backend should delete drop?
    return show_drops(drop_id, "drop deleted")


@app.route('/unsubscribe/<drop_id>')
def unsubscribe(drop_id):
    # if no drop is selected
        # Do nothing
    # else
        # communicate change to backend
    return show_drops(None, "unsubscribed")


# Request a change to the selected drop
@app.route('/request_change/<drop_id>')
def request_change(drop_id):
    # if no drop is seleted
        # Do nothing
    # else
        # communicate change to backend
    return show_drops(drop_id, "change requested")


@app.route('/')
def startup():
    return show_drops(None, None)


@app.route('/<drop_id>', methods=['GET', 'POST'])
def show_drops(drop_id=None, message=None):
    owned_drops = get_owned_drops()
    subscribed_drops = get_subscribed_drops()
    selected_drop = []

    if drop_id is not None:
        selected_drop = get_selected_drop(drop_id)

    performed_action = []  # REMOVE WHEN BACKEND COMMUNICATION IS ADDED

    if message is not None:
        performed_action = {'description': message}

    # File Actions
    if request.method == 'POST':
        if request.form.get('type') == 'open_file':
            open_file_location('PUT PROPER LOCATION HERE')
        elif request.form.get('type') == 'remove_file':
            remove_file('PUT PROPER LOCATION HERE')

    return render_template(
        'show_drops.html', selected=selected_drop, subscribed=subscribed_drops,
        owned=owned_drops, action=performed_action,
    )


@app.route('/initialize', methods=['GET', 'POST'])
def initialize():
    return startup()
    # if request.method == 'POST':
    #    session['logged_in'] = True
    #    flash('You were logged in')
    #    return redirect(url_for('show_drops'))
    # return render_template('initialize.html')
