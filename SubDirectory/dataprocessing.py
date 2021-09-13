

""" 
Gets the news media data from MediaClouds API from the selected media sources and saves all stories and their data in a csv file: story-list.csv
"""
import pandas as pd
import os, mediacloud.api
from textblob import TextBlob
import matplotlib.pyplot as plt
import mediacloud.tags
from datetime import date
from io import BytesIO
from dotenv import load_dotenv
import csv
from textblob import TextBlob

load_dotenv()  # load config from .env file
mc = mediacloud.api.MediaCloud(os.getenv('MC_API_KEY'))
mediacloud.__version__

# set variables
start_date = date(2019,1,1)
end_date = date(2020,12,31)
date_range = mc.dates_as_query_clause(start_date, end_date) # initial time range: year 2019

ratio_dict= {}
people_dict={}
media_dict= {
    1: 'New York Times', 
    39590: 'South China Morning Post',
    1094: 'BBC',
    65173: 'Peoples Daily'
    }

# Function to get story Data of media queries
# args: medialist : list with selected mediaIDs for MediaCloudAPI queries
def getData(medialist):
    for i in medialist:
        query =f' "Hong Kong" AND (protest* OR unrest OR "Anti-Extradition" OR "democracy movement" OR assembly OR demonstration* OR “human chain” OR rally) and media_id:{i}'
        
        get_ratios(query,i)

        # creates all_stories for the first media source, then just adds stories from others to the list
        if i == list(media_dict.keys())[0]:
            all_stories= all_matching_stories(mc, query, date_range)
            print(len(all_stories))
        else:
            stories= all_matching_stories(mc, query, date_range)
            all_stories= stories + all_stories
            print(len(all_stories))

# formatting publish date and analyse sentiment of title using TextBlob
    for s in all_stories:
        blob= TextBlob(s['title'])
        s['subjectivity']= blob.sentiment.subjectivity
        s['polarity'] = blob.sentiment.polarity
        s['publish_date'] = pd.Timestamp(s['publish_date']).date() #removes time from date for easier processing
    
    
    # now write the CSV
    fieldnames = ['stories_id', 'publish_date', 'title', 'url', 'language', 'media_id', 'media_name', 'media_url', 'subjectivity', 'polarity']
    with open('story-list.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for s in all_stories:
            writer.writerow(s)

    #Create Pandas Dataframe from csv list
    story_df= pd.read_csv('story-list.csv',parse_dates=True, squeeze=True)

    return(story_df)
    

#Function to fetch all stories from a media outlet, returns all stories
# args: mc_client: media cloud object initiated with API client
#       q: query
#       fq: datarange query
def all_matching_stories(mc_client, q, fq):
    last_id = 0
    more_stories = True
    stories = []
    while more_stories:
        page = mc_client.storyList(q, fq, last_processed_stories_id=last_id, rows=500, sort='processed_stories_id')
        print("  got one page with {} stories".format(len(page)))
        if len(page) == 0:
            more_stories = False
        else:
            stories += page
            last_id = page[-1]['processed_stories_id']
    return stories        

def get_ratios(q,i):
    # the number of stories alone does not say much, instead the ratio to overall stories is interesting to see the attention a media source gave to a topic
    relevant_stories = mc.storyCount(q, date_range)
    total_stories = mc.storyCount(f'media_id:{i}', date_range)
    source_ratio = relevant_stories['count'] / total_stories['count']

    #print('{:.2%} of 2019 {} stories are about "hong kong protest"'.format(source_ratio, i))
    ratio_dict[i]=source_ratio
    print(ratio_dict)

def get_people(q,i):
    people_results = mc.storyTagCount(q, date_range, tag_sets_id=mediacloud.tags.TAG_SET_CLIFF_PEOPLE)
    people_dict[i]= people_results
    #print(people_dict)
    print(people_dict)

    people_df = pd.DataFrame(people_results[:10])
    people_df = people_df[["count", "label"]]
    people_df = people_df.set_index('label')
    people_df['media_source'] = i
    print(people_df)

# sample size (sentences) has big influence over results
def get_wordcount(q,i):
    results = mc.wordCount(q, date_range,sample_size=10000, include_stats=1) #size 1000 - 100.000
    df= pd.DataFrame(results[:20])
    df = df[["count", "term"]]
    df['media_id'] = i
    df= df.sort_values('count',ascending=False)
    return(df)

def get_orgscount(q,i):
    results = mc.storyTagCount(q, date_range, tag_sets_id=mediacloud.tags.TAG_SET_CLIFF_ORGS)
    df= pd.DataFrame(results[:20])
    df = df[["count", "description"]]
    df['media_id'] = i
    df= df.sort_values('count',ascending=False)
    return(df)

#getData(media_dict)

