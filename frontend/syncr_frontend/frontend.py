import platform
import subprocess
from os import path
from os import scandir

from flask import flash
from flask import Flask
from flask import render_template
from flask import request

from .communication import send_request

app = Flask(__name__)  # create the application instance
app.config.from_object(__name__)  # load config from this file , frontend.py

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='development key',
    TEMPLATES_AUTO_RELOAD=True,
))
app.config.from_envvar('SYNCR_SETTINGS', silent=True)

# Global Variables
curr_action = ''
current_drop_path = ''
testing = False
home_path = path.expanduser('~')[1:]

# Backend Access Functions


def send_message(message):
    """
    Sends given message to backend. Waits for a response
    or until TIMEOUT

    :param message: message sent to backend
    :return: response from server
    """

    response = send_request(message)

    return response


def open_file_location(file_path):
    """
    Opens the location of the file

    :param file_path: Path of the file on computer
    """
    # Placeholder until backend communication is set-up
    file_path = path.dirname(path.abspath(__file__))

    op_sys = platform.system()
    if op_sys == 'Windows':
        subprocess.Popen(['explorer', file_path])
    if op_sys == 'Linux':
        subprocess.Popen(['xdg-open', file_path])
    if op_sys == 'Darwin':
        subprocess.Popen(['open', file_path])


def get_owned_subscribed_drops():
    """
    :return: Gets a tuple of of dictionaries in format (owned drop dict, \
            subscribed drop dict)
    """
    message = {
        'action': 'get_owned_subscribed_drops',
    }

    response = send_message(message)

    return response.get('requested_drops_tuple')


# Return dictionary for selected drop
def get_selected_drop(drop_id):
    """
    :param drop_id: Selected drop
    :return: Dictionary for selected drop
    """
    message = {
        'drop_id': drop_id,
        'action': 'get_selected_drop',
    }

    response = send_message(message)

    drop = response.get('requested_drops')

    return drop


def get_pending_changes(drop_id):
    message = {
        'drop_id': drop_id,
        'action': 'get_pending_changes',
    }

    response = send_message(message)

    drop = response.get('requested_drops')

    return drop


def is_in_drop_list(drop_id, drop_list):
    """
    :param drop_id: ID of the drop.
    :param drop_list: List of drops
    :return: Returns True if the given drop_id exists in the drop list.
    """

    in_list = False

    for drop in drop_list:
        if drop.get('drop_id') == drop_id:
            in_list = True

    return in_list


def get_drop_id(file_path):
    """
    Gets drop id from file path

    :param file_path: File path that contains drop ID
    :return: drop ID
    """

    reached_slash = False
    drop_string = ''

    for letter in file_path:
        if not reached_slash:
            if letter == '/':
                reached_slash = True
            else:
                drop_string = drop_string + letter

    return drop_string


def get_file_name(file_path):
    """
    Gets file name from file path

    :param file_path: File path that contains file name
    :return: file name
    """

    file_name = ''

    for letter in file_path:
        if letter == '/':
            file_name = ''
        else:
            file_name = file_name + letter

    return file_name


def set_curr_action(action_update):
    """
    Sets the global variable to the current pressed
    button

    :param action_update: name of action
    """

    global curr_action
    curr_action = action_update


@app.route('/create_drop/<path:current_path>')
def create_drop(current_path):
    """
    This function provides the UI with the prompt to create a drop

    :return: response that triggers the UI prompt.
    """

    set_curr_action('create_drop')

    return show_drop(
        None,
        None,
        current_path,

    )


@app.route('/subscribe_to_drop/<path:current_path>')
def subscribe_to_drop(current_path):
    """
    This function provides the UI with the prompt to subscribe to a drop.

    :return: response that triggers the UI prompt.
    """

    set_curr_action('subscribe_to_drop_directory')

    return show_drop(
        None,
        None,
        current_path,
    )


@app.route('/subscribe_to_drop_with_directory/<path:drop_path>')
def subscribe_to_drop_with_directory(drop_path):
    """
    Given a directory, requests user to provide drop code
    for a drop to subscribed to and then save in that location
    """
    set_curr_action('subscribe_to_drop_name')

    return show_drop(
        None,
        None,
        drop_path,
    )


@app.route('/initialize_drop/<path:drop_path>')
def initialize_drop(drop_path):
    """
    After inputting a name, a drop is created with said name.

    :return: Message sent back to frontend.
    """
    response = ''

    if drop_path is None:
        flash('Cannot create drop. No directory was selected.')
        has_response = False
    else:
        message = {
            'action': 'initialize_drop',
            'directory': '/' + drop_path,
        }
        has_response = True
        response = send_message(message)

    if has_response:
        message = response.get('message')
    else:
        message = None

    set_curr_action(None)

    return show_drop(
        None,
        message,
    )


@app.route('/subscribe', methods=['POST'])
def input_drop_to_subscribe(drop_code=None, drop_path=None):
    """
    After inputting a name, user is subscribed to drop if it exists

    :return: Message sent to frontend.
    """
    if drop_code is None:
        result = request.form.get('drop_to_subscribe_to')
        path = request.form['drop_path']
    else:
        result = drop_code
        path = drop_path

    message = {
        'action': 'input_drop_to_subscribe',
        'drop_id': result,
        'directory': '/' + path,
    }

    response = send_message(message)
    return show_drop(
        None,
        response.get('message'),
    )


@app.route('/share_drop/<drop_id>')
def share_drop(drop_id):
    """
    Sends 'share drop' message to backend

    :param drop_id: Drop to be shared
    :return: backend sends back message with info to share drop
    """

    set_curr_action('share drop')

    message = {
        'drop_id': drop_id,
        'action': 'share_drop',
    }
    response = send_message(message)
    # TODO: remove drop_id after socket setup
    result = response.get('message')
    return show_drop(drop_id, result)


@app.route('/view_owners/<drop_id>/add/', methods=['GET', 'POST'])
def add_owner(drop_id, owner_id=None):
    """
    Communicate with backend to add an owner to specified drop

    :param drop_id: ID of drop
    :return: display updated owners body of page
    """
    if owner_id is None:
        if request.method == 'POST':
            if request.form.get('owner_id') is None:
                return view_owners(drop_id)

        new_owner_id = request.form.get('owner_id')
    else:
        new_owner_id = owner_id

    message = {
        'drop_id': drop_id,
        'owner_id': new_owner_id,
        'action': 'add_owner',
    }

    response = send_message(message)

    if response.get("Success") is False:
        return view_owners(drop_id, response.get('message'))

    return view_owners(drop_id)


@app.route('/view_owners/<drop_id>/remove/<owner_id>')
def remove_owner(drop_id, owner_id):
    """
    Communicate with backend to remove an owner from specified drop

    :param drop_id: ID of drop
    :param owner_id: ID of owner to remove from drop
    :return: display updated owners body of page
    """

    message = {
        'drop_id': drop_id,
        'owner_id': owner_id,
        'action': 'remove_owner',
    }

    response = send_message(message)

    if response.get("Success") is False:
        return view_owners(drop_id, response.get('message'))

    return view_owners(drop_id)


@app.route('/view_owners/<drop_id>')
def view_owners(drop_id, message=None):
    """
    Update current action to display list of owners

    :param drop_id: ID of drop to view owners
    :param message: message from owner action if any
    :return: display owners on body of page
    """
    set_curr_action('owners')

    return show_drop(drop_id, message)


@app.route('/whitelist/<drop_id>')
def whitelist(drop_id):
    """
    Communicate with backend to whitelist node

    :param drop_id: ID of drop where node is whitelisted
    :return: Display prompt on page to whitelist node
    """
    set_curr_action('whitelist')

    return show_drop(drop_id, "node whitelisted")


@app.route('/delete_drop/<drop_id>')
def delete_drop(drop_id):
    """
    Sends the 'delete drop' message to backend

    :param drop_id: name of the drop to be deleted
    :return: drop is removed from backend and frontend
    """

    set_curr_action('delete drop')

    message = {
        'drop_id': drop_id,
        'action': 'delete_drop',
    }

    response = send_message(message)

    return show_drop(
        response.get('drop_id'),
        response.get('message'),
    )


@app.route('/unsubscribe/<drop_id>')
def unsubscribe(drop_id):
    """
    Communicate with backend to unsubscribe from drop

    :param drop_id: ID of drop to be unsubscribed
    :return: UI and backend update to not have subscribed drop.
    """

    set_curr_action('unsubscribe')
    message = {
        'drop_id': drop_id,
        'action': 'unsubscribe',
    }
    response = send_message(message)
    result = response.get('message')

    if response.get('success') is True:
        return show_drop(None, result)
    else:
        return show_drop(drop_id, result)


@app.route('/new_version/<drop_id>')
def new_version(drop_id):
    """
    Tells backend to create new version from
    changed files for specified drop

    :param drop_id: drop to create new version for
    :return: renders web page based off backend response
    """

    message = {
        'action': 'new_version',
        'drop_id': drop_id,
    }

    response = send_message(message)

    return show_drop(
        response.get('drop_id'),
        response.get('message'),
    )


@app.route('/')
def startup():
    set_curr_action(None)
    return show_drop(None, None)


@app.route('/drop/<drop_id>', methods=['GET', 'POST'])
def show_drops(drop_id=None, message=None, current_path=None):
    set_curr_action(None)
    return show_drop(drop_id, message, current_path)


def show_drop(drop_id=None, message=None, current_path=None):
    """
    Main action handler. Shows drops

    :param drop_id: ID of current drop
    :param message: Message from a particular action
    :param current_path: current directory recognized
    :return: renders web page based off of drop and action.
    """
    global testing

    drop_tups = get_owned_subscribed_drops()
    if drop_tups is not None:
        owned_drops = drop_tups[0]
        subscribed_drops = drop_tups[1]
    else:
        owned_drops = []
        subscribed_drops = []

    selected_drop = []
    new_ver = None
    permission = None

    file_status = {}
    added = []

    if drop_id is not None:

        if curr_action:
            selected_drop_info = get_selected_drop(drop_id) or {}
        else:
            selected_drop_info = get_pending_changes(drop_id) or {}
        selected_drop = selected_drop_info.get('drop')
        if selected_drop is not None:

            if is_in_drop_list(drop_id, owned_drops):
                permission = "owned"
            else:
                permission = "subscribed"

            # Check if new version can be created
            pending_changes = selected_drop_info.get('pending_changes', {})
            added = pending_changes.get('added', [])
            removed = pending_changes.get('removed', [])
            changed = pending_changes.get('changed', [])
            unchanged = pending_changes.get('unchanged', [])
            for f in removed:
                file_status[f] = 'removed'
            for f in changed:
                file_status[f] = 'changed'
            for f in unchanged:
                file_status[f] = 'unchanged'
            version_update = any([added, removed, changed])
            if version_update and is_in_drop_list(drop_id, owned_drops):
                new_ver = True
                flash('NEW VERSION can be made. Select NEW VERSION.')

    performed_action = []  # REMOVE WHEN BACKEND COMMUNICATION IS ADDED

    if message is not None:
        performed_action = {'description': message}
        if not testing:
            flash(message)

    # File Actions
    if not testing and request.method == 'POST':
        if request.form.get('type') == 'open_file':
            open_file_location('PUT PROPER LOCATION HERE')

    # Directory Stepping
    folders = []
    if current_path:
        try:
            with scandir('/' + current_path) as entries:
                for entry in entries:
                    if not entry.is_file() and entry.name[0] != '.':
                        folders.append(entry.name)
        except Exception as e:
            flash(e)
            folders = []
    else:
        current_path = home_path

    if not testing:
        return render_template(
            'show_drops.html',
            selected=selected_drop,
            subscribed=subscribed_drops,
            owned=owned_drops,
            action=performed_action,
            selec_act=curr_action,
            new_version=new_ver,
            permission=permission,
            directory=current_path,
            directory_folders=folders,
            file_status=file_status,
            added=added,
        )
    else:
        return {
            'selected_drop': selected_drop,
            'subscribed_drops': subscribed_drops,
            'owned_drops': owned_drops,
            'performed_action': performed_action,
            'curr_action': curr_action,
            'new_version': new_ver,
            'permission': permission,
        }


class FrontendHook:

    def __init__(self):
        """
        Enable Testing Mode and pull default drop data from backend
        """
        global testing
        testing = True

        backend_data = startup()
        self.update_hook(backend_data)

    def update_hook(self, backend_data):
        self.selected_drop = backend_data.get('selected_drop')
        self.subscribed_drops = backend_data.get('subscribed_drops')
        self.owned_drops = backend_data.get('owned_drops')
        self.action = backend_data.get('performed_action')
        self.selected_action = backend_data.get('curr_action')
        self.versions = backend_data.get('file_versions')

    def send_message(self, message):
        return send_message(message=message)

    def get_owned_subscribed_drops(self):
        return get_owned_subscribed_drops()

    def get_selected_drop(self, drop_id):
        return get_selected_drop(drop_id=drop_id)

    def initialize_drop(self, drop_path):
        self.update_hook(initialize_drop(drop_path=drop_path))

    def input_drop_to_subscribe(self, drop_code):
        self.update_hook(input_drop_to_subscribe(drop_code=drop_code))

    def share_drop(self, drop_id):
        self.update_hook(share_drop(drop_id=drop_id))

    def add_owner(self, drop_id, owner_id):
        self.update_hook(add_owner(drop_id=drop_id, owner_id=owner_id))

    def remove_owner(self, drop_id, owner_id):
        self.update_hook(remove_owner(drop_id=drop_id, owner_id=owner_id))

    def delete_drop(self, drop_id):
        self.update_hook(delete_drop(drop_id=drop_id))

    def unsubscribe(self, drop_id):
        self.update_hook(unsubscribe(drop_id=drop_id))
