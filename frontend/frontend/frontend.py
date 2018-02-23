from flask import Flask
from flask import render_template

app = Flask(__name__)  # create the application instance
app.config.from_object(__name__)  # load config from this file , frontend.py

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='development key',
    TEMPLATES_AUTO_RELOAD=True,
))
app.config.from_envvar('SYNCR_SETTINGS', silent=True)

# Backend Access Functions


def get_owned_drops():
    # Placeholder until backend communication is set-up
    # TODO: validate data structure
    return [{'name': 'O_Drop_1'}, {'name': 'O_Drop_2'}]


def get_subscribed_drops():
    # Placeholder until backend communication is set-up
    # TODO: validate data structure
    return [{'name': 'S_Drop_1'}, {'name': 'S_Drop_2'}, {'name': 'S_Drop_3'}]


def get_selected_drop(drop_id):
    # if drop does not exist -> return default drop display
    return {'name': drop_id}


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


@app.route('/<drop_id>')
def show_drops(drop_id=None, message=None):
    owned_drops = get_owned_drops()
    subscribed_drops = get_subscribed_drops()
    selected_drop = []
    if drop_id is not None:
        selected_drop = get_selected_drop(drop_id)
    performed_action = []  # REMOVE WHEN BACKEND COMMUNICATION IS ADDED
    if message is not None:
        performed_action = {'description': message}
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
