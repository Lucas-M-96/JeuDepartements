#!/usr/bin/python3.12
# -*- coding: utf-8 -*-

from flask import Flask, render_template, session, request, redirect, flash, url_for, send_from_directory, jsonify
from datetime import datetime, timedelta
import pandas as pd
import re
import os
import sys
import pathlib
import sqlite3
import uuid
import random
import json
from datetime import datetime, timezone
# import cryptocode

# GLOBAL VARIABLES

datetime_str_format = '%Y-%m-%d %H:%M:%S'

# front_path = pathlib.Path(__file__).absolute().parent
# base_path = front_path.parent

app = Flask(__name__)
app.config['SECRET_KEY']='app_departements'
base_url = '/departements'

# retrieve departements database
df_dpts = pd.read_csv('./../data_sources/dpt_source.csv')
df_dpts.loc[:, 'index'] = df_dpts.loc[:, 'code_departement']
df_dpts = df_dpts.set_index('index')
# df_dpts = df_dpts.head(3)

# static elements to be sent to frontend
static_lists_dic = {}

# prepare list of fields (order number and real name)
# note: order of both lists below must match, and will be the order displayed in app
dpt_fields_list = ['nom_departement', 'code_departement', 'prefecture_departement', 'nom_region']
dpt_fields_display_name_list = ['Nom du département', 'Numéro du département', 'Préfecture du département', 'Région du département']
if sorted(dpt_fields_list) != sorted(list(df_dpts.columns)):
    print()
    print("WARNING: fields_list does not match department source data")
    print(f"field list: {dpt_fields_list.sort()}")
    print(f"department source columns: {list(df_dpts.columns).sort()}")
    print()
dpt_fields_dic = dict(zip(dpt_fields_list, dpt_fields_display_name_list))
static_lists_dic['dpt_fields_dic'] = dpt_fields_dic
static_lists_dic['base_url'] = base_url

# retrieve list of options for all fields (for autocomplete)
for field in dpt_fields_list:
    static_lists_dic[field] = sorted(list(set(df_dpts[field].values.tolist())))

# initialize connecton to db
db_path = "./../departementsApp.db"
con = sqlite3.connect(db_path)
cur = con.cursor()


# create db table if not already existing
cur.execute(f"""CREATE TABLE IF NOT EXISTS solo_trainings(
                    training_uuid TEXT PRMIARY KEY,
                    player_name TEXT,
                    dpt_field_question TEXT,
                    remaining_dpt_nums_list TEXT,
                    current_dpt_number TEXT,
                    {' INTEGER, '.join([dpt_field + '_score' for dpt_field in dpt_fields_list])} INTEGER,
                    total_answers INTEGER,
                    training_start_time TEXT,
                    training_end_time TEXT,
                    training_duration TEXT)""")
con.commit()

# crypto_key_path = base_path / 'crypto_key'
# with open(crypto_key_path, 'r') as f:
#     crypto_key = f.read().rstrip()

# UTIL FUNCTIONS

# # remove logs and config when deleting a job
# def remove_associated_files(resa_id):
#     log_path = base_path / 'logs_resa' / f"{resa_id}.log"
#     if log_path.exists():
#         os.remove(log_path)
#     else:
#         print(f"WARNING : log file associated to job {resa_id} could not be deleted")

# dupplicate outputs to stdout and log file (flush in real time)

# class DupplicatedStdout(object):
#     def __init__(self, name):
#         self.file = open(name, 'a')
#         self.stdout = sys.stdout
#         sys.stdout = self
#     def __del__(self):
#         sys.stdout = self.stdout
#         self.file.close()
#     def write(self, data):
#         self.file.write(data)
#         self.stdout.write(data)
#     def flush(self):
#         self.file.flush()
#         self.stdout.flush()

# class DupplicatedStderr(object):
#     def __init__(self, name):
#         self.file = open(name, 'a')
#         self.stderr = sys.stderr
#         sys.stderr = self
#     def __del__(self):
#         sys.stderr = self.stderr
#         self.file.close()
#     def write(self, data):
#         self.file.write(data)
#         self.stderr.write(data)
#     def flush(self):
#         self.file.flush()



# WEB APPLICATION

# display starting page
@app.route(base_url, methods=['GET'])
def start_page():
    return render_template('start_page.html', df_dpts=df_dpts, static_lists_dic=static_lists_dic)


def get_next_turn_dpt_row(dpt_nums_list):

    # pick a department randomly
    next_dept_idx = random.randint(0, len(dpt_nums_list) - 1)
    next_dept_code = dpt_nums_list[next_dept_idx]
    next_dept_row = df_dpts.loc[next_dept_code, :]

    return next_dept_row


@app.route(f'{base_url}/start_training', methods=['POST'])
def start_training():

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # define list of dpts for the game
    selected_region = request.form["selected-region"]
    if selected_region != 'Toutes les régions':
        df_dpts_filtered = df_dpts.loc[df_dpts['nom_region'] == selected_region]
    else:
        df_dpts_filtered = df_dpts.copy()
    game_dpt_nums_list = df_dpts_filtered['code_departement'].to_list()

    # select first dpt to be asked
    next_dept_row = get_next_turn_dpt_row(game_dpt_nums_list)
    remaining_dpt_nums_list = game_dpt_nums_list.copy()
    remaining_dpt_nums_list.remove(next_dept_row['code_departement'])

    #  generate new training uuid and start time
    training_uuid = str(uuid.uuid4())
    start_time = datetime.utcnow().replace(tzinfo=timezone.utc)
    start_time_str = start_time.isoformat()
    # retrieve new training settings
    dpt_field_question = request.form["dpt-field-question"]
    player_name = request.form['player-name']

    # initialize training session (cookies and db)
    session['training_uuid'] = training_uuid
    insert_values = (
        (
            training_uuid,
            player_name,
            dpt_field_question,
            json.dumps(remaining_dpt_nums_list),
            next_dept_row['code_departement']
        ) + tuple(
             [0 for i in range(len(static_lists_dic['dpt_fields_dic']))]
        ) + (
            0,
            start_time_str,
            start_time_str,
            0
        ))
    insert_query = f"""INSERT INTO solo_trainings
                       VALUES ( {', '.join(['?' for i in range(len(insert_values))])} )"""
    cur.execute(insert_query, insert_values)
    con.commit()

    # prepare data to be sent to UI
    updated_data_for_ui = {
        'training_is_finished': False,
        'dpt_field_question': dpt_field_question,
        'question': next_dept_row[dpt_field_question],
        'dpt_row': next_dept_row.to_dict(),
        'remaining_questions': len(df_dpts_filtered),
        'total_answers': 0,
        'scores': {},
        'training_start_time': start_time_str}
    for dpt_field in dpt_fields_list:
        updated_data_for_ui['scores'][dpt_field] = 0

    return render_template('training.html', updated_data_for_ui=updated_data_for_ui, static_lists_dic=static_lists_dic)


def retrieve_training_state(training_uuid):

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # query relevant rows
    queried_cols = ['dpt_field_question', 'remaining_dpt_nums_list', 'current_dpt_number', 'total_answers', 'training_start_time', 'training_end_time']
    queried_cols = queried_cols + [dpt_field + '_score' for dpt_field in static_lists_dic['dpt_fields_dic'].keys()]
    res = cur.execute(f"SELECT {', '.join(queried_cols)} FROM solo_trainings WHERE training_uuid=?", (training_uuid,))
    res = res.fetchall()[0]  # only one row is returned in this case
    
    #  parse and store results in a dictionnary
    training_state = {}
    for i, col in enumerate(queried_cols):
        if col == 'remaining_dpt_nums_list':
            # this field must be parsed because it is a list
            training_state[col] = json.loads(res[i])
        elif col in ['training_start_time', 'training_end_time']:
            training_state[col] = datetime.fromisoformat(res[i])
        else:
            training_state[col] = res[i]

    return training_state


def update_db(training_state, udated_fields):
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    training_uuid = session['training_uuid']

    update_query = f"""UPDATE solo_trainings
                       SET {', '.join([key + '=?' for key in udated_fields])}
                       WHERE training_uuid=?"""
    update_values = tuple([training_state[key] for key in udated_fields]) + (training_uuid,)

    cur.execute(update_query, update_values)
    con.commit()


@app.route(f'{base_url}/training', methods=['POST'])
def training():

    training_uuid = session['training_uuid']

    # retrieve training state from db
    training_state = retrieve_training_state(training_uuid)

    # last_dept_row = df_dpts.loc[last_dpt_num, :]
    remaining_dpt_nums_list = training_state['remaining_dpt_nums_list']

    # # update score, total answers and time
    # for dpt_field in static_lists_dic['dpt_fields_dic'].keys():
    #     if dpt_field != training_state['dpt_field_question']:
    #         if request.form[dpt_field + '-input'] == last_dept_row[dpt_field]:
    #             training_state[dpt_field + '_score'] = training_state[dpt_field + '_score'] + 1
    # training_state['total_answers'] = training_state['total_answers'] + 1
    # end_time = datetime.now()
    # training_state['training_end_time'] = end_time.strftime(datetime_str_format)
    # training_state['training_duration'] = str(end_time - training_state['training_start_time']).split('.')[0][:8].zfill(8)

    # prepare data to be sent to UI
    updated_data_for_ui = {
        'training_is_finished': True,  # if there is a next question this will be overwritten
        'remaining_questions' : 0,  #  if there is a next question this will be overwritten
        'dpt_field_question': training_state['dpt_field_question'],
        'total_answers': training_state['total_answers'],
        'training_start_time': training_state['training_start_time'].isoformat(),
        'scores': {}}
    for dpt_field in dpt_fields_list:
        updated_data_for_ui['scores'][dpt_field] = training_state[dpt_field + '_score']

    # select next dpt to be asked and update remaning nums (if tere are still questions to be asked)
    if len(remaining_dpt_nums_list) > 0:
        next_dept_row = get_next_turn_dpt_row(remaining_dpt_nums_list)
        remaining_dpt_nums_list.remove(next_dept_row['code_departement'])

        training_state['current_dpt_number'] = next_dept_row['code_departement']
        training_state['remaining_dpt_nums_list'] = remaining_dpt_nums_list

        # send info to UI as well
        updated_data_for_ui['training_is_finished'] = False
        updated_data_for_ui['remaining_questions'] = len(remaining_dpt_nums_list) + 1
        updated_data_for_ui['question'] = next_dept_row[training_state['dpt_field_question']]
        updated_data_for_ui['dpt_row'] = next_dept_row.to_dict()

    #  update db with new information
    training_state['remaining_dpt_nums_list'] = json.dumps(training_state['remaining_dpt_nums_list'])
    update_db(training_state, ['current_dpt_number', 'remaining_dpt_nums_list'])   

    return render_template('training.html', updated_data_for_ui=updated_data_for_ui, static_lists_dic=static_lists_dic)


@app.route(f'{base_url}/update_scores', methods=['POST'])
def update_scores():
    training_state = request.json
    print(type(training_state))
    update_db(training_state, list(training_state.keys()))

    return jsonify({'message': 'Scores updated successfully'})


@app.route(f'{base_url}/score_board', methods=['GET'])
def score_board():

    # initiate connection to db
    con = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM solo_trainings", con)


    # clean dataset and select relevant columns
    score_cols = [col for col in df.columns if 'score' in col]
    df['total_score'] = 0
    for col in score_cols:
        df['total_score'] = df['total_score'] + df[col]
    df = df.rename(columns={"dpt_field_question": "game_mode"})
    score_board_cols = ['player_name', 'training_start_time', 'training_duration', 'game_mode'] + score_cols + ['total_score', 'total_answers']
    score_board_cols_display = ['Joueur', 'Date', 'Durée', 'Mode de jeu', 'Noms', 'Numéros', 'Préfectures', 'Régions', 'Total', 'Tours']
    df = df.loc[:, score_board_cols]


    # keep only rows that are relevant for the score board (top 10)
    df_list = []
    for game_mode in ['nom_departement', 'code_departement', 'prefecture_departement', 'nom_region']:
        for score_col in list(filter(lambda col: 'score' in col, df.columns)):
            df_tmp = df.copy()
            df_tmp['rank'] = (
                df_tmp
                .sort_values(['total_score', 'training_duration'], ascending=[False, False])
                .groupby(['game_mode'])
                .cumcount() + 1)
            df_tmp = df_tmp.loc[df_tmp['rank'] <= 10].drop('rank', axis=1)
            df_list.append(df_tmp)
    df_score_board = pd.concat(df_list).reset_index(drop=True).drop_duplicates()

    # convert to a format easier to manipulate in js
    score_board_data = df_score_board.to_dict('records')
    static_lists_dic['score_table_columns'] = dict(list(zip(score_board_cols, score_board_cols_display)))
    return render_template('score_board.html', static_lists_dic=static_lists_dic, score_board_data=score_board_data)


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')


# # -- Create new reservation job
# @app.route('/schedule_job', methods=['POST'])
# def schedule_job():

#     # collect reservation settings from html form
#     config = {}
#     config["email"] = request.form["email"]
#     pw_encoded = cryptocode.encrypt(request.form["pw"], crypto_key)
#     config["pw"] = pw_encoded
#     target_locations = []
#     for num in location_choices:
#         location = request.form[f"location_{num}"]
#         if location != "No location":
#             target_locations.append(location)
#     target_locations = ', '.join(target_locations)
#     config["target_locations"] = target_locations
#     config["target_date"] = request.form["target_date"]
#     config["target_hours"] = request.form["hours"]
#     config["mate_name"] = request.form["mate_name"]
#     config["mate_first_name"] = request.form["mate_first_name"]
#     config["short_sleeping_time"] = request.form["short_sleeping_time"]
#     config["long_sleeping_time"] = request.form["long_sleeping_time"]

#     # generate resa and job metadata

#     resa_id = datetime.now().strftime('%Y-%m-%d-%H%M%S-%f')
#     resa_id += "_-_" + (config["email"].split("@")[0]).replace(".","")
#     resa_id += "_" + nornmalize_str(config["mate_first_name"]) + nornmalize_str(config["mate_name"])
#     resa_id += "_-_" + config["target_locations"].split(', ')[0].split(" ")[-1]
#     resa_id += "_" + config["target_date"]
#     resa_id += "_" + config["target_hours"].replace(';','-')

#     opening_time = datetime.strptime(config["target_date"] + '-08h',"%Y-%m-%d-%Hh") - timedelta(days=6)
#     opening_time_gap = opening_time - datetime.now()
#     reservation_time = datetime.strptime(config["target_date"] + '-' + sorted(config["target_hours"].split(';'))[0], "%Y-%m-%d-%Hh")
#     reservation_time_gap = reservation_time - datetime.now()
#     minutes_margin = 4
#     if (opening_time_gap < timedelta(seconds=0)) & (reservation_time_gap > timedelta(hours=1)):
#         job_time = datetime.now() + timedelta(minutes=2)
#     elif opening_time_gap > timedelta(minutes=minutes_margin):
#         job_time = opening_time - timedelta(minutes=2)
#     elif reservation_time_gap < timedelta(hours=1):
#         job_time = None
#         flash("INVALID TARGET DATE :target date is either past or in less than 1 hour")
#     else:
#         job_time = None
#         flash(f"INVALID TIME : you cannot create a job for a reservation in exactly 6 days less than {minutes_margin} minutes before 8AM")

#     # insert job in database
#     if job_time:
#         job_time_str = job_time.strftime('%Y-%m-%d - %H:%M')
        
#         con = sqlite3.connect(db_path)
#         cur = con.cursor()

#         nb_cols = len(pd.read_sql_query("SELECT * FROM jobs LIMIT 1", con).columns)
#         insert_query = f"""INSERT INTO jobs VALUES ({', '.join(['?'] * nb_cols)})"""
#         insert_values = (resa_id, job_time_str) + tuple(config.values())
#         cur.execute(insert_query, insert_values)

#         con.commit()
#         con.close()

#     return redirect('/')
