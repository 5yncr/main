import platform
import subprocess
from os import path

from flask import flash
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


def send_message(message):
    # Sends given message to backend
    # Wait for a response or until TIMEOUT
    # If error_message is not None, display error_message
    # Else display success_message

    # Example response for initial UI setup
    # TODO: remove when socket communication is setup
    response = {
        'drop_id': message.get('drop_id'),
        'file_name': message.get('file_name'),
        'action': message.get('action'),
        'message': "Generic Message For " + message.get('action'),
        'success': True,
        'requested_drops': (
            {
                'drop_id': 'o1',
                'name': 'O_Drop_1',
                'version': None,
                'previous_versions': [],
                'primary_owner': 'owner_id',
                'other_owners': [],
                'signed_by': 'owner_id',
                'files': [
                    {'name': 'FileOne'},
                    {'name': 'FileTwo'},
                    {'name': 'FileThree'},
                    {'name': 'FileFour'},
                    {'name': 'Folder'},
                ],
            },
            {
                'drop_id': 'o2',
                'name': 'O_Drop_2',
                'version': None,
                'previous_versions': [],
                'primary_owner': 'owner_id',
                'other_owners': [],
                'signed_by': 'owner_id',
                'files': [],
            },
        ),
    }
    return response


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


@app.route('/remove_file/<drop_id>/<file_name>')
def remove_file(drop_id, file_name):
    # Remove file at specified location from drop info
    message = {
        'drop_id': drop_id,
        'file_name': file_name,
        'action': 'rf',
    }
    response = send_message(message)
    # TODO: Remove file name after proper communication is set up
    return show_drops(
        response.get('drop_id'),
        response.get('message') + " " + response.get("file_name"),
    )


# Return list of owned drop dictionaries
def get_owned_drops():
    message = {
        'action': 'get_owned',
    }

    response = send_message(message)

    return response.get('requested_drops')


# Return list of subscribed drop dictionaries
def get_subscribed_drops():
    message = {
        'action': 'get_owned',
    }

    send_message(message)
    # response = send_message(message)

    # TODO: Return generic response once socket communication is setup
    # return response.get('requested_drops')
    return (
        {
            'drop_id': 's1',
            'name': 'S_Drop_1',
            'version': None,
            'previous_versions': [],
            'primary_owner': 'owner_id',
            'other_owners': [],
            'signed_by': 'owner_id',
            'files_hash': ["files_hash"],
            'files': [
                    {'name': 'FileOne'},
                    {'name': 'FileTwo'},
                    {'name': 'FileThree'},
                    {'name': 'FileFour'},
                    {'name': 'Folder'},
            ],
            'sig': ["header_signature"],
        },
        {
            'drop_id': 's2',
            'name': 'S_Drop_2',
            'version': None,
            'previous_versions': [],
            'primary_owner': 'owner_id',
            'other_owners': [],
            'signed_by': 'owner_id',
            'files_hash': ["files_hash"],
            'files': [
                    {'name': 'FileOne'},
                    {'name': 'FileTwo'},
                    {'name': 'FileThree'},
            ],
            'sig': ["header_signature"],
        },
    )


# Return dictionary for selected drop
def get_selected_drop(drop_id):
    message = {
        'drop_id': drop_id,
        'action': 'get_selected',
    }

    response = send_message(message)

    drop_list = response.get('requested_drops')

    if drop_list is None:
        return None
    else:
        return drop_list[0]


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

    file_path = None  # TODO: implement file picker (tkinter not working)

    if file_path is None:
        result = None
    else:
        message = {
            'drop_id': drop_id,
            'action': 'cp',
            'file_path': file_path,
        }
        response = send_message(message)
        # TODO: remove filename after socket setup
        result = response.get('message') + ' ' + file_path

    return show_drops(drop_id, result)


@app.route('/share_drop/<drop_id>')
def share_drop(drop_id):
    message = {
        'drop_id': drop_id,
        'action': 'share',
    }
    response = send_message(message)
    # TODO: remove drop_id after socket setup
    result = response.get('message') + ' share id for ' + drop_id
    return show_drops(drop_id, result)


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
    message = {
        'drop_id': drop_id,
        'action': 'unsub',
    }
    response = send_message(message)
    result = response.get('message')
    # TODO: remove drop_id after socket setup
    result = result + ' ' + drop_id

    if response.get('success') is True:
        return show_drops(None, result)
    else:
        return show_drops(drop_id, result)


# Request a change to the selected drop
@app.route('/request_change/<drop_id>')
def request_change(drop_id):
    message = {
        'drop_id': drop_id,
        'action': 'change',
    }
    response = send_message(message)
    result = response.get('message')
    return show_drops(drop_id, result)


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
        # TODO: Remove when sockets are setup
        selected_drop['name'] = drop_id
        selected_drop['permission'] = get_permission(drop_id)

    performed_action = []  # REMOVE WHEN BACKEND COMMUNICATION IS ADDED

    if message is not None:
        performed_action = {'description': message}
        flash(message)

    # File Actions
    if request.method == 'POST':
        if request.form.get('type') == 'open_file':
            open_file_location('PUT PROPER LOCATION HERE')

    return render_template(
        'show_drops.html', selected=selected_drop, subscribed=subscribed_drops,
        owned=owned_drops, action=performed_action,
    )
