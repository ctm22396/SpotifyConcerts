# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 12:10:30 2015

@author: christianmeyer
"""

import os
import numpy as np
import json
import urllib
import pandas as pd
import re
import spotify as sfy

def login_spotify(user, passw, directory):
    os.chdir(directory)
    
    global sess
    try:
        sess = sfy.Session()
    except:
        pass
    
    loop = sfy.EventLoop(sess)
    loop.start()
    sess.login(user,passw)
    return sess

def get_playlists(sess):
    playlists = sess.get_published_playlists()
    
    playlist_df = {}
    for playlist in playlists:
        try:
            name = playlist.name.title()
            link = playlist.link.uri.title()
            proc_link = ':'.join([x.lower() for x in link.split(':')[:-1]] + [link.split(':')[-1]])
            playlist_df[name] = dict(link=proc_link, playlist=playlist)
        except:
            pass
    return playlist_df

def select_playlist(playlist_df, playlist_name):
    my_playlist = playlist_df[playlist_name]["playlist"]
    return my_playlist

def get_artists(my_playlist):
    track_df = {}
    artist_list = []
    for track in my_playlist.tracks:
        try:
            name = track.name.title()
            artists = ', '.join([x.name for x in track.artists])
            
            for artist in track.artists:
                artist_list.append(artist.name)
                
            link = track.link.uri.title()
            proc_link = ':'.join([x.lower() for x in link.split(':')[:-1]] + [link.split(':')[-1]])
            track_df[name] = dict(artists=artists, link=proc_link, track=track)
        except:
            pass
    
    artist_list = np.unique(np.array(artist_list))
    return artist_list


def get_metro_id():
    songkick_api_key = 'jwzmbEyCAIwD7HCy'
    
    f = urllib.urlopen('http://api.songkick.com/api/3.0/search/locations.json?location=clientip&apikey=%s' % songkick_api_key)
    page_dict = json.load(f)
    metro_id = page_dict[u'resultsPage'][u'results'][u'location'][0]['metroArea']['id']
    country = page_dict[u'resultsPage'][u'results'][u'location'][0]['metroArea']['country']['displayName']
    city = page_dict[u'resultsPage'][u'results'][u'location'][0]['metroArea']['displayName']
    return metro_id, country, city


def get_similiar_artists(artist_list):
    songkick_api_key = 'jwzmbEyCAIwD7HCy'
    
    similar_artist_df = pd.DataFrame(artist_list.T, columns=['artist_name'])
    for artist in artist_list:
        artist = re.sub(r'[^\x20-\x7e]', '', artist)
        f1 = urllib.urlopen('http://api.songkick.com/api/3.0/search/artists.json?query="%s"&apikey=%s' % (artist, songkick_api_key))
        
        try:
            artist_id = json.load(f1)["resultsPage"]['results']['artist'][0]['id']
        except:
            continue
        
        f2 = urllib.urlopen('http://api.songkick.com/api/3.0/artists/%s/similar_artists.json?apikey=%s' % (artist_id, songkick_api_key))
        page_dict = json.load(f2)
        
        sim_artist = []
        try:
            for entry in page_dict['resultsPage']['results']['artist']:
                sim_artist.append(entry['displayName'])
        except:
            continue
        
        similar_artist_df = similar_artist_df.append(pd.DataFrame(np.array(sim_artist).T, columns=['artist_name']), ignore_index=True)
    return pd.DataFrame(similar_artist_df.artist_name.unique().T, columns=["artist_name"])

def get_concerts(metro_id):
    songkick_api_key = 'jwzmbEyCAIwD7HCy'
    metro_df = pd.DataFrame()
    for i in range(1,51):
        f = urllib.urlopen('http://api.songkick.com/api/3.0/metro_areas/%s/calendar.json?apikey=%s&page=%s' % (metro_id, songkick_api_key, i) )
        page_dict = json.load(f)
        try:
            metro_df = metro_df.append(pd.DataFrame.from_dict(page_dict["resultsPage"]["results"]["event"]), ignore_index=True)
        except:
            break  
        
    count = 0
    for i in range(len(metro_df)):
        venue_name = metro_df['venue'][i]["displayName"]
        date = metro_df['start'][i]['date']
        time = metro_df['start'][i]['time']
        popularity = metro_df['popularity'][i]
        series = metro_df["series"][i]
        concert_id = metro_df['id'][i]
        link = metro_df["uri"][i]
        
        for j, entry in enumerate(metro_df.performance[i]):
            artist = entry["artist"]            
            artist_name = artist["displayName"]
            artist_id = artist['id']
            artist_billing = entry['billing']
            if i == j == 0:
                new_metro_df = pd.DataFrame([[artist_name, artist_id, artist_billing,
                                              date, time, venue_name, link, concert_id, popularity, series]],
                                              columns = ['artist_name', 'artist_id', 'artist_billing',
                                              'date', 'time', 'venue_name', 'link', 'concert_id', 'popularity', 'series'])
            else:       
                new_metro_df.loc[count] = [artist_name, artist_id, artist_billing,
                                         date, time, venue_name, link, concert_id, popularity, series]
            count += 1
            
            artist_name = artist_id = artist_billing = artist = pd.np.NaN
        date = time = venue_name = popularity = series = pd.np.NaN
    return new_metro_df
    
def match_artists(artist_df, metro_df):    
    my_artists = artist_df.artist_name.unique().tolist()
    touring_artist = metro_df.artist_name.unique().tolist()
    joined = list(set(my_artists) & set(touring_artist))
    joined_df = metro_df[metro_df.concert_id.isin(metro_df[metro_df.artist_name.isin(joined)].concert_id.values.tolist())]
    return joined_df
