
# Run this Dash app with `python app.py`
# visit http://127.0.0.1:8050/ in web browser.

####################################### Import dependencies and other files #####################################################
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
import os, mediacloud.api
from io import BytesIO
from dotenv import load_dotenv
import sys
import csv
from datetime import date
from SubDirectory import dataprocessing


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

#Variable to switch to offline testing without requesting new
OFFLINE = False

####################################### Set variables & import data #####################################################
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


#define app colors
colors = {
    'background': '#f7f7f5',
    'text': '#2a2a2a'
}

#define colors for different media sources
media_colors = {
    "South China Morning Post": "#EFB938",
    "New York Times": "#647CAA",
    "BBC": "#7BB48D",
    "Peoples Daily": "#C0003A",
    "english.people.com.cn": "#C0003A"
}

# gets data from csv document which is updated by the dataprocessing file continously
# this makes it possible to both use online + offline, as well as update the data, eg. change sources /timespan

if OFFLINE:
    print("OFFLINE MODE")
    story_df= pd.read_csv('story-list.csv',parse_dates=True, squeeze=True)
    word_df= pd.read_csv('word_df.csv',parse_dates=True, squeeze=True)
    orgs_df= pd.read_csv('orgs_df.csv',parse_dates=True, squeeze=True)

    print(story_df.groupby('media_id')['subjectivity'].mean())
    
else:
    print("ONLINE MODE")
    #story_df= pd.read_csv('story-list.csv',parse_dates=True, squeeze=True)

    story_df= dataprocessing.getData(dataprocessing.media_dict)
    print(story_df.groupby('media_id')['subjectivity'].mean())

    #calculate most used words (for some reason does not want to work in dataprocessing file)
    word_df= pd.DataFrame()
    for i in dataprocessing.media_dict:
        query = f'"Hong Kong" AND (protest* OR unrest OR "Anti-Extradition" OR "democracy movement" OR assembly OR demonstration* OR “human chain” OR rally) and media_id:{i}'
        df= dataprocessing.get_wordcount(query,i)
        df['media_name'] = dataprocessing.media_dict[i]
        word_df = word_df.append(df)    
    word_df.to_csv('word_df.csv')

    orgs_df= pd.DataFrame()
    for j in dataprocessing.media_dict:
        query = f'"Hong Kong" AND (protest* OR unrest OR "Anti-Extradition" OR "democracy movement" OR assembly OR demonstration* OR “human chain” OR rally) and media_id:{j}'
        df= dataprocessing.get_orgscount(query,j)
        df['media_name'] = dataprocessing.media_dict[j]
        orgs_df = orgs_df.append(df)   
    orgs_df.to_csv('orgs_df.csv')

####################################### Create Visualisations & other dashboard elements ####################################

# create a scatterplot
fig = px.scatter(story_df, x="publish_date",y="polarity",
                 #size="subjectivity", 
                 color="media_name", color_discrete_map= media_colors, hover_name="title",
                )
fig.update_layout(hovermode="x unified")


# Chart to compare coverage amount of different news sources

fig2 = px.histogram(story_df, x="publish_date", marginal="rug",color="media_name", hover_name= 'title', hover_data={'publish_date':False}, color_discrete_map= media_colors, barmode='group')
fig2.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        hovermode="x unified",
        yaxis=dict(
        title='Articles published',
        ),
        xaxis=dict(
        title='Date',
        )
    )

fig3= px.scatter(story_df, x="publish_date", color="polarity", color_continuous_scale= px.colors.diverging.balance, y="media_name", hover_name="title")
fig3.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        yaxis=dict(
        title='Media Outlet',
        ),
        xaxis=dict(
        title='Date',
        )
)
fig3.update_traces(marker_opacity=1, marker_symbol= 42, marker_size= 50)

fig4 =px.bar(word_df, x="count", y= "term", barmode="group", color= "media_name", color_discrete_map= media_colors,)
fig4.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        height=600,
        yaxis=dict(
        title='Term',
        categoryorder= 'total descending'
        ),
        xaxis=dict(
        title='Count',
        )
    )

fig5 =px.bar(orgs_df, x="count", y= "description", color= "media_name", color_discrete_map= media_colors, width=30)

# Text to go with the visualisations
# also make this responsive in app callback?
markdown_text = f''' 
### Development of the Hong Kong protests in the News

How much news content does each media source dedicate to the topic of the Hong Kong protests? \n
The following graph compares the number of news articles published about the topic by different news sources. \n
While the number of stories alone does not say much, it is interesting to compare what time each news media picked up \n
a news event or to explore when the number of articles spiked and what the headlines were around that time. \n
The ratio to overall stories of each source reveals the attention a media source gave to a topic: &nbsp   
\n
**The percentage of a sources' news articles that mentioned the Hong Kong protests:**   \n
{dataprocessing.media_dict.get(1, 0)} : **{dataprocessing.ratio_dict.get(1,0):.2%}** \n
{dataprocessing.media_dict.get(39590,0)} : **{dataprocessing.ratio_dict.get(39590,0):.2%}** \n
{dataprocessing.media_dict.get(1094, 0)} : **{dataprocessing.ratio_dict.get(1094,0):.2%}** \n
{dataprocessing.media_dict.get(65173,0)} : **{dataprocessing.ratio_dict.get(65173,0):.2%}** \n
'''

# create small tables from text? or visualise the numbers in a better way?

markdown_text2 = f''' 
### Sentiment and Polarity of Article Headlines

Since news headlines set the tone for an article and reach an even larger audience than the article text itself, it is vital that they are neutral and objective. \n
Looking at headlines that are subjective or overly positive/negative in tone can reveal biases of news sources. \n
The calculated polarity values range from from -1 (negative tone) to +1 (positive tone), the subjectivity values from 0 (objective) to 1 (subjective). \n
**Average polarity values for the headlines of each news source:**   \n
{dataprocessing.media_dict.get(1, 0)} : **{story_df[story_df['media_name']=='New York Times']['polarity'].mean():.2}** \n

{dataprocessing.media_dict.get(39590,0)} : **{story_df[story_df['media_name']=='BBC']['polarity'].mean():.2}** \n

{dataprocessing.media_dict.get(1094, 0)} : **{story_df[story_df['media_name']=='South China Morning Post']['polarity'].mean():.2}** \n

{dataprocessing.media_dict.get(65173,0)} : **{story_df[story_df['media_name']=='english.people.com.cn']['polarity'].mean():.2}** \n
'''

markdown_text3 = f''' 
### Taking a closer look at the most used words

Analysing the most used words can show each news source's perspective, as well as which aspects of the news events they focus on. \n
Instances of news bias can be revealed for example through different labels chosen for the same entity or event.
'''

#display data table
def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])

####################################### Set app layout + HTML #####################################################
    
app.layout = html.Div(style={'backgroundColor': colors['background'], 'font-family': "Verdana"}, children=[   html.H1(
        children='News Explorer',
        style={
            'textAlign': 'center',
            'color': colors['text'],
            'letter-spacing': '5px',
            'font-weight': 'lighter',
            'padding-top': '1em',
        }
    ),
    
    #display subtitle
    html.Div(children='visualising digital news coverage', style={
        'textAlign': 'center',
        'color': '#5a5a5a',
        'margin-bottom': '3em'
    }),

    #Dropdown menu to select multiple news sources
    html.Label('Select a News Sources to explore'),
    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': 'New York Times (US)', 'value': 1},
            {'label': 'South China Morning Post (Hong Kong)', 'value': 39590},
            {'label': 'BBC (UK)', 'value': 1094},
            {'label': 'Peoples Daily (China)', 'value': 65173},
        ],
        value=[1, 39590, 1747,65173],
        multi=True,
        style= {
            'color': colors['text'],
        }
    ),
    
    #Date Picker to change time range
    html.Label('Pick a date range '),
    dcc.DatePickerRange(
        id='my-date-picker-range',
        min_date_allowed=min(story_df['publish_date']),
        max_date_allowed=max(story_df['publish_date']),
        initial_visible_month=date(2019, 1, 1),
        end_date=date(2019, 12, 31),
        start_date=min(story_df['publish_date']),
        clearable= False,
    ),

    #display markdown text
    dcc.Markdown(
        id="text",
        children=markdown_text,
        style={'backgroundColor': '#f0f0f0', 'margin' : '42px', 'padding': '8px'}
    ),

    # display graph
    dcc.Graph(
        id='bar-chart',
        figure=fig2
    ),

    #display markdown text
    dcc.Markdown(
        id="text2",
        children=markdown_text2,
        style={'backgroundColor': '#f0f0f0', 'margin' : '42px', 'padding': '8px'}
    ),
    
    # display graph
    dcc.Graph(
        id='rug-chart',
        figure=fig3
    ),

     # display graph
    dcc.Graph(
        id='scatter-plot',
        figure=fig
    ),

    #display markdown text
    dcc.Markdown(
        id="text3",
        children=markdown_text3,
        style={'backgroundColor': '#f0f0f0', 'margin' : '42px', 'padding': '8px'}
    ),

    # display graph
    dcc.Graph(
        id='word-bars',
        figure=fig4
    ),

    # # display graph
    # dcc.Graph(
    #     id='fifth-graph',
    #     figure=fig5
    # ),

    # # display table
    # html.Div(children=[
    # html.H4(children='All Stories'),
    # generate_table(story_df)
    # ],
    # style={
    #         'textAlign': 'center',
    #         'color': colors['text']
    #     })
])
####################################### Callback functions #####################################################

#Callback for dropdown menu (media sources) and date range picker -> Updates graphs
@app.callback(
    Output('bar-chart', 'figure'),
    Output('scatter-plot', 'figure'),
    Output('rug-chart', 'figure'),
    Output('word-bars', 'figure'),
    Input('dropdown', 'value'),
    [Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')])

def update_figure(selected_media, start_date, end_date):
    time_df = story_df.loc[(story_df['publish_date'] >= start_date) & (story_df['publish_date'] < end_date)]
    filtered_df= time_df[time_df.media_id.isin(selected_media)]
    filtered_word_df= word_df[word_df.media_id.isin(selected_media)]
    

    fig = px.scatter(filtered_df, x="publish_date",y="polarity",
                 marginal_y="rug", opacity= 0.6,
                 color="media_name", color_discrete_map= media_colors, hover_name="title",
                )

    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        yaxis=dict(
        title='Polarity',
        )
    )

    fig.update_xaxes(
        dtick="M1",
        title= "Date",
        tickformat="%b\n%Y",
        ticklabelmode="period"
        )

    fig.update_traces(marker_opacity=0.8)

    fig2 = px.histogram(filtered_df, x="publish_date", marginal="rug",color="media_name", hover_name= 'title', hover_data={'publish_date':False}, color_discrete_map= media_colors, barmode= 'group') 
    
    fig2.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        hovermode="x unified",
        yaxis=dict(
        title='Articles published',
        ),
        xaxis=dict(
        title='Date',
        )
    )


    fig3= px.scatter(filtered_df, x="publish_date", color="subjectivity", #color_continuous_scale= px.colors.diverging.balance,
    color_continuous_scale= px.colors.sequential.matter, y="media_name", hover_name="title")

    fig3.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        yaxis=dict(
        title='Media Outlet',
        ),
        xaxis=dict(
        title='Date',
        )
    )
    fig3.update_traces(marker_opacity=1, marker_symbol= 42, marker_size= 50)


    #new word counts
    

    # calculating new word counts -> works, but takes too long, slows overall performance
    # would only work if the word_df is differently structured, so that it can be filtered by time

    # word_df= pd.DataFrame()
    # for i in selected_media:
    #     df= pd.DataFrame()
    #     query = f'"Hong Kong" AND (protest* OR unrest OR "Anti-Extradition" OR "democracy movement*" OR "extradition") and media_id:{i}'
    #     df= dataprocessing.get_wordcount(query,i)
    #     #df['media_name'] = dataprocessing.media_dict[i]
    #     word_df = word_df.append(df)
    

    fig4 =px.bar(filtered_word_df, x="count", y= "term", barmode="group", color= "media_name", color_discrete_map= media_colors,)
    fig4.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        height=800,
        yaxis=dict(
        title='Term',
        tickmode='linear', # displays every label instead of only every other,
        categoryorder= 'total ascending'
        ),
        xaxis=dict(
        title='Count',
        )
    )

    return fig2, fig, fig3, fig4


if __name__ == '__main__':
    app.run_server(debug=True)