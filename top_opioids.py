#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import string

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import register_adapter, AsIs

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import plotly.express as px
from dash.dependencies import Input, Output, State

import chart_studio.plotly as py
import plotly.graph_objects as go

from sodapy import Socrata

conn = psycopg2.connect("dbname=opioids user=postgres")
cur = conn.cursor()

# In[2]:

par_tup = (AsIs('gennme'),
       AsIs('number_of_prescriptions'),
       AsIs('state_code'))

query = sql.SQL(""" select %s, %s, %s
                from sdud_merged;
                """)

opi_data = pd.read_sql_query(query,
                       con = conn,
                       params =  par_tup)

# In[3]:

opi_data = opi_data.groupby(['state_code', 'gennme'], as_index = False)['number_of_prescriptions'].sum()

opi_data.rename(columns = {'number_of_prescriptions' : 'tot_rx'}, inplace = True)

opi_data['rank'] = opi_data.groupby('state_code', as_index = False)['tot_rx'].rank(ascending = False)

tot_stat = opi_data.groupby('state_code', as_index = False).agg({'tot_rx' : 'sum'})

tot_stat.rename(columns = {'tot_rx' : 'tot_state'}, inplace = True)

opi_data = opi_data.merge(tot_stat, on = 'state_code')

opi_data['perc'] = 100 * (opi_data['tot_rx'] / opi_data['tot_state'])

keep_drugs = opi_data['gennme'][(opi_data['perc'] >= 2.0) & (opi_data['rank'] <= 10.0)].unique()

opi_data = opi_data[opi_data['gennme'].isin(keep_drugs)]

# In[4]:

measure_options = [{'label': 'Market Share', 'value' : 'perc'},
                       {'label': 'Total Rx', 'value' : 'tot_rx'},
                       {'label': 'State Rank', 'value' : 'rank'}]

measure_plot = {}

for m in measure_options:

    measure_plot[m['value']] = m['label']

generic_options = {}

generic_plot = {}

generic_options = [{'label': c, 'value': c} for c in opi_data['gennme'].unique()]

for g in generic_options:

    if 'acetaminophen' in g['label']:

        g['label'] = g['label'].split(' ')[1] + ' ' + g['label'].split(' ')[0]

    g['label'] = string.capwords(g['label'])

    generic_plot[g['value']] = g['label']

layout_dict = {}

layout_dict['perc'] = go.Layout(
    annotations=[
        go.layout.Annotation(
            align = 'left',
            showarrow=False,
            text='Notes:<br>'+
                 '[1] Market share is calculated as share of all opioids prescribed through Medicaid in each state<br>'
                 'Sources:<br>' +
                 '[1] https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data/index.html' +
                 '<br>' +
                 '[2] https://www.cdc.gov/drugoverdose/resources/data.html',
            xanchor='right',
            x=0.75,
            yanchor='top',
            y=0.05
        )])

layout_dict['rank'] = go.Layout(
    annotations=[
        go.layout.Annotation(
            align = 'left',
            showarrow=False,
            text='Notes:<br>'+
                 '[1] Rank is based on all opioids prescribed through Medicaid in each state<br>'
                 'Sources:<br>' +
                 '[1] https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data/index.html' +
                 '<br>' +
                 '[2] https://www.cdc.gov/drugoverdose/resources/data.html',
            xanchor='right',
            x=0.75,
            yanchor='top',
            y=0.05
        )])

layout_dict['tot_rx'] = go.Layout(
    annotations=[
        go.layout.Annotation(
            align = 'left',
            showarrow=False,
            text='Sources:<br>' +
                 '[1] https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data/index.html' +
                 '<br>' +
                 '[2] https://www.cdc.gov/drugoverdose/resources/data.html',
            xanchor='right',
            x=0.75,
            yanchor='top',
            y=0.05
        )])


# In[5]:


# adapted from https://community.plotly.com/t/updating-a-dropdown-menus-contents-dynamically/4920/4
# exxt_ss = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

# app = JupyterDash(__name__, external_stylesheets = ext_ss)

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__)

# external_stylesheets=external_stylesheets)

app.layout = html.Div(
    children=[
        html.Div(className='row',
                 children=[
                    html.Div(className='four columns div-user-controls',
                             children=[
                                 html.H2('DASH - STOCK PRICES'),
                                 html.P('Visualising time series with Plotly - Dash.'),
                                 html.P('Pick one or more stocks from the dropdown below.'),
                                 html.Div(
                                     children=[
                                         dcc.Dropdown(id='measure-dropdown',
                                                      options=measure_options,
                                                      clearable = False,
                                                      value = 'perc',
                                                      ),

                                        html.Hr(),

                                        dcc.Dropdown(
                                            id='drug-dropdown',
                                            clearable = False,
                                            options = generic_options,
                                            value = 'acetaminophen hydrocodone'
                                        ),
                                     ])
                                ]
                             ),

                    html.Div(className='eight columns div-for-charts bg-grey',
                             children=[
                                 dcc.Graph(id='example-graph')
                             ])
                              ])
        ]

)

# app.layout = html.Div(style={'fontFamily': 'Helvetica',
#                             'fontSize': 14,
#                             'fontColor': 'black'}, children = [
#
#     dcc.Dropdown(
#
#         id='measure-dropdown',
#         options = measure_options,
#         clearable = False,
#         value = 'perc'
#
#     ),
#
#     html.Hr(),
#
#     dcc.Dropdown(
#         id='drug-dropdown',
#         clearable = False,
#         options = generic_options,
#         value = 'acetaminophen hydrocodone'
#     ),
#
#     html.Hr(),
#
#     dcc.Graph(
#         id = 'example-graph'
#     )
#
# ])

# @app.callback(
#     dash.dependencies.Output('drug-dropdown', 'label'),
#     [dash.dependencies.Input('measure-dropdown', 'value')])
#
# def set_cities_options(selected_measure):
#     return generic_options
#
# @app.callback(
#     dash.dependencies.Output('drug-dropdown', 'value'),
#     [dash.dependencies.Input('drug-dropdown', 'label')])
#
# def set_cities_value(available_options):
#     return available_options[0]['value']

@app.callback(
    dash.dependencies.Output('example-graph', 'figure'),
    [dash.dependencies.Input('measure-dropdown', 'value'),
     dash.dependencies.Input('drug-dropdown', 'value')])

def set_display_children(selected_measure, selected_drug):

    opi_sum = opi_data[opi_data['gennme'] == selected_drug]

    opi_sum = opi_sum.dropna()

    meas = measure_plot[selected_measure]

    drug = generic_plot[selected_drug]

    fig = go.Figure(data = go.Choropleth(
                locations = opi_sum['state_code'], # Spatial coordinates
                z = opi_sum[selected_measure].astype(float), # Data to be color-coded
                locationmode = 'USA-states', # set of locations match entries in `locations`
                colorscale = 'Reds',
                colorbar_title = meas,),
                layout = layout_dict[selected_measure])

    if selected_measure == 'rank':

        fig = go.Figure(data = go.Choropleth(
                locations = opi_sum['state_code'], # Spatial coordinates
                z = opi_sum[selected_measure].astype(float), # Data to be color-coded
                locationmode = 'USA-states', # set of locations match entries in `locations`
                colorscale = 'Reds',
                reversescale = True,
                colorbar = {'title' : meas},),
                layout = layout_dict['rank'])

    fig.update_layout(
        title_text = meas + ' of ' + drug + ' Prescriptions by State Medicaid in 2018',
        template = 'plotly',
        font = {'family': 'Helvetica', 'color' : 'black'},
        geo_scope = 'usa', # limite map scope to USA
    )

    return fig

if __name__ == "__main__":
    app.run_server(debug=True)


# In[ ]:
