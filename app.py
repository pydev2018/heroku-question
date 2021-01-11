import pandas as pd
import numpy as np
import os
from ftplib import FTP
from time import sleep
import time

import dash
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import sqlite3
#from app import app



external_stylesheets = [dbc.themes.LUX]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)




red_button_style = {'background-color': 'red',
'color': 'white',
'height': '60px',
'width': '120px',
'margin-top': '10px',
'margin-left': '10px'
}


##################################

app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(html.Img(src="/assets/heroku.JPG", height="80px"), className="mb-4 mt-4")
            
        ]),
        
        
        
        dbc.Row([
            dbc.Col(dbc.Col(html.H1("Heroku Test Real Time Heatmap"), className="mb-4"))
        ]),
        
        
        dbc.Row([
            dbc.Col(html.H5(children='Web App to test live plot on Heroku '), className="mb-4")
        ]),
        
        dbc.Row([
            dbc.Col(html.H6(children='---------------------------------------------------------------------'), className="text-left mt-4 mb-4")
        ]),
        
        dbc.Row([
            dbc.Col(html.H5(children='Constant value to query the DB'), className="text-left mt-4 mb-4"),
            dbc.Col(dcc.Input(id='line_name', className="mt-3 mb-4", type="number", placeholder='Value is 4', value=4, disabled=True), width=6)
                                                                                
        ]),
        
        dbc.Row([
            dbc.Col(html.Button('START_PLOT', id='qc_start',n_clicks=0, style=red_button_style), className='mb-4')
        ]),
        

    dbc.Row([
        dbc.Col(dbc.Card(html.H4(children='Heat Maps',
                                    className="text-center text-light bg-dark"), body=True, color="dark")
                , className="mt-4 mb-4")
        ]),

    dbc.Row([
        dbc.Col(html.H5(children='SOURCE - 1', className="text-center"),
                width=6, className="mt-4"),
        dbc.Col(html.H5(children='SOURCE - 2', className="text-center"), width=6,
                className="mt-4"),
        ]),
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='bp_s1'), width=6 ),
        dbc.Col(dcc.Graph(id='bp_s2' ), width=6 )
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Interval( 
        id = 'graph_update', 
        interval = 3*1000, 
        n_intervals = 0)
        )
        
        
    ]),
    
    dbc.Row([
        dbc.Col(html.H2(id='hidden-div', style= {'display': 'none'} )),
        dbc.Col(html.H6(id='input-div', style= {'display': 'none'})),
        dbc.Col(html.H6(id='button-div', children=0, style= {'display': 'none'}))

        ])
    
    
        
        
        ])
    
])

cols = [  'shot' , 'chan' , 'peak_amplitude',  'onset_time_(ms)', 'bubble_period_(ms)']
cols_bubble_period  = [ 'shot' , 'chan' ,  'bubble_period_(ms)']
#cols_peak_onset_time  = [  'shot' , 'chan', 'onset_time_(ms)']
#cols_peak_amplitude  = [ 'shot' , 'chan'  ,'peak_amplitude' ]

all_results =  pd.DataFrame(columns = cols)


def get_df_size(seq, DB_FILE):
    """
    Get number of rows 
    in the sequence
    """
    
    con = sqlite3.connect(str(DB_FILE))
    len_statement = f'SELECT * FROM Bubble_QC WHERE sequence = {seq} ;'
    length = len(pd.read_sql_query(len_statement,con))
    return length 


def get_plot_data(start, end, DB_FILE, seq):
    """
    Query plot data
    """
    con = sqlite3.connect(str(DB_FILE))
    statement = f'SELECT * FROM Bubble_QC WHERE sequence = {seq} AND rowid > "{start}" AND rowid <= "{end}";'
    df = pd.read_sql_query(statement, con)
    return df



def df_to_plotly(df):
    return {'z': df.values.tolist(),
            'x': df.columns.tolist(),
            'y': df.index.tolist()}


@app.callback(
    Output('qc_start', 'disabled'),
    [Input('qc_start', 'n_clicks')]
)
def hide_newbutton(n_clicks):
	if n_clicks == 0: return False
	else:
		print('Disabling the button')
		return True



@app.callback(Output('input-div', 'children'),
              [Input('qc_start', 'n_clicks')],
              state=[State(component_id='line_name', component_property='value')])
def update_div(n_clicks, input_value):
    return input_value



@app.callback(Output('hidden-div', 'children'),
    [Input('qc_start', 'n_clicks'),
    State('line_name', 'value')]
    )

def extract_data(n_clicks, value):
    if value is None or n_clicks == 0:
        raise dash.exceptions.PreventUpdate()

    i=0
    global all_results
    while i < int(get_df_size(value, 'plot_data_seq_04.db' )):
        all_results = all_results.append((get_plot_data(i, i+180, 'plot_data_seq_04.db', value)).drop(['sequence'], axis=1))
        i = i+ 180
        sleep(2)



@app.callback(
    Output('bp_s1', 'figure'),
    [Input('graph_update', 'n_intervals'),
    Input('qc_start', 'n_clicks')]
    
)
def update_bp_1(n_clicks, n_intervals):
    if n_clicks == 1:
        raise dash.exceptions.PreventUpdate()
    
    global all_results
    all_results_1 = all_results.apply(pd.to_numeric)
    #all_results_1 = all_results_1.drop_duplicates()
    #all_results_1.to_csv('all_results.csv')
    df_s1 = all_results_1.loc[all_results_1['chan'] <=18]
    df_s1_bp = df_s1[cols_bubble_period]
    #print(df_s1_bp)
    #df_s1_bp.to_csv('test_data.csv')
    df_s1_pivoted = df_s1_bp.pivot(  'chan', 'shot', 'bubble_period_(ms)')
    
    data = go.Heatmap(df_to_plotly(df_s1_pivoted) ,  colorscale='rainbow', zmin=30.0, zmax=210.0)
    return {'data': [data], 
            'layout' : go.Layout(xaxis_nticks=20, yaxis_nticks=20)} 




@app.callback(
    Output('bp_s2', 'figure'),
    [Input('graph_update', 'n_intervals'),
    Input('qc_start', 'n_clicks')]
    
)
def update_bp_2(n_clicks, n_intervals):
    if n_clicks == 1:
        raise dash.exceptions.PreventUpdate()
    
    global all_results
    all_results_1 = all_results.apply(pd.to_numeric)
    #all_results_1 = all_results_1.drop_duplicates()
    #all_results_1.to_csv('all_results.csv')
    df_s1 = all_results_1.loc[all_results_1['chan'] >=19]
    df_s1_bp = df_s1[cols_bubble_period]
    #print(df_s1_bp)
    #df_s1_bp.to_csv('test_data.csv')
    df_s1_pivoted = df_s1_bp.pivot(  'chan', 'shot', 'bubble_period_(ms)')
    
    data = go.Heatmap(df_to_plotly(df_s1_pivoted) ,  colorscale='rainbow' , zmin=30.0, zmax=210.0)
    return {'data': [data], 
            'layout' : go.Layout(xaxis_nticks=20, yaxis_nticks=20)} 

        

server = app.server

server.secret_key = os.environ.get('SECRET_KEY', 'my-secret-key')


if __name__ == '__main__':
    app.run_server(debug=True)

 