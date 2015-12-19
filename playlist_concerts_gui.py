# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 19:24:07 2015

@author: christianmeyer
"""

import sys
import os
import pandas as pd
import numpy as np
import urllib
import base64
from PIL import Image
from io import BytesIO
import webbrowser

import playlist_concerts as pc

if sys.version.split('.')[0] == '2':
    import Tkinter as tk
else:
    import tkinter as tk
    
class AutoScrollbar(tk.Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        tk.Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise tk.TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise tk.TclError, "cannot use place with this widget"    

class ConcertLinksPage(tk.Frame):
    
    def __init__(self, parent, controller):
        
        self.controller = controller
        self.parent = parent        
        tk.Frame.__init__(self, parent)
        
    def callback(self, link):
        webbrowser.open_new(link)
        
    def populate(self):
        row_count = 2
        col_count = 0
        concert_id = ''
        for concert in self.controller.joined_df.iterrows():
            
            if not concert[1].concert_id == concert_id:            
                link = concert[1].link
                html = urllib.urlopen(link).read()
                image_url = 'http:'+html.split('class="profile-picture event"')[1].split(' ')[1].split('src=')[1].strip('"')
                image = urllib.urlopen(image_url).read()
                image_pil = Image.open(BytesIO(image))
                image_pil.save('./tmp/test.gif', 'gif')
                img_obj = tk.PhotoImage(file='./tmp/test.gif')
                img_label = tk.Label(self, image=img_obj, cursor='hand2')
                img_label.image = img_obj 
                img_label.grid(row=row_count, column=col_count)
                col_count += 1
                
                string = tk.StringVar()
                text_label = tk.Label(self, text=concert[1].artist_name + ' - ' + concert[1].venue_name, textvariable=string, fg="blue", cursor="hand2")
                string.set(concert[1].artist_name + ' - ' + concert[1].venue_name)
                text_label.grid(row=row_count, column=col_count)
                col_count += 1
                
                img_label.bind("<1>", lambda e,link=link:self.callback(link))
                text_label.bind("<1>", lambda e,link=link:self.callback(link))                
                
                concert_id = concert[1].concert_id
                
                if col_count == 6:
                    col_count = 0
                    row_count += 1
                    
            else:
                string.set(string.get() + '\n' + concert[1].artist_name + ' - ' + concert[1].venue_name)
        
        self.controller.canvas.create_window(0, 0, anchor=tk.NW, window=self.parent)

        self.parent.update_idletasks()
        
        self.controller.canvas.config(scrollregion=self.controller.canvas.bbox("all")) 


class ArtistsPage(tk.Frame):

    def __init__(self, parent, controller):
        
        self.controller = controller
        self.parent = parent        
        tk.Frame.__init__(self, parent)
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_columnconfigure(0, weight=1)   
        self.grid_rowconfigure(1, weight=0)
    
    def make_buttons(self):
        concerts_butt = tk.Button(self, text='Find Concerts', command = self.forward_concerts)
        concerts_butt.grid(row = 0, columnspan = 20)        
        
        similar_butt = tk.Button(self, text='Similar Artists', command = self.goto_similar)
        similar_butt.grid(row = 1, columnspan = 20)
        
    def populate(self, artists):
        row_count = 2
        col_count = 0
        for artist in artists:
            self.grid_rowconfigure(row_count, weight=0)
            self.grid_columnconfigure(col_count, weight=1)            
            artist_label = tk.Label(self, text = artist)
            artist_label.grid(row = row_count, column = col_count, sticky='n')
            row_count += 1
            if row_count == 34:
                row_count = 2
                col_count += 1
    
        back_butt = tk.Button(self, text='Back', command = lambda: self.controller.show_frame(self.controller.last_page))
        back_butt.grid(row = 35, columnspan = col_count + 1)
        
        self.controller.canvas.create_window(0, 0, anchor=tk.NW, window=self.parent)

        self.parent.update_idletasks()
        
        self.controller.canvas.config(scrollregion=self.controller.canvas.bbox("all"))         
        
    def goto_similar(self):
        self.controller.artists_df = pc.get_similiar_artists(self.controller.artists)
        self.controller.similar_artists = self.controller.artists_df.artist_name.values.tolist()        
        
        for widget in self.controller.frames[SimilarArtistsPage].winfo_children():
            widget.destroy()
        
        self.controller.frames[SimilarArtistsPage].make_buttons()
        self.controller.frames[SimilarArtistsPage].populate(self.controller.similar_artists)
        self.controller.last_page = ArtistsPage
        self.controller.show_frame(SimilarArtistsPage)  
        
    def forward_concerts(self):
        metro_id, country, city = pc.get_metro_id()
        
        if len(self.controller.metro_df) == 0:
            self.controller.metro_df = pc.get_concerts(metro_id)
            
        self.controller.joined_df = pc.match_artists(self.controller.artists_df, self.controller.metro_df)
        self.controller.last_page = ConcertLinksPage
        self.controller.frames[ConcertLinksPage].populate()
        self.controller.show_frame(ConcertLinksPage)        
        
        
class SimilarArtistsPage(ArtistsPage):
    
    def __init__(self, parent, controller):
        
        ArtistsPage.__init__(self, parent, controller)
        
    def make_buttons(self):
        concerts_butt = tk.Button(self, text='Find Concerts', command = self.forward_concerts)
        concerts_butt.grid(row = 0, columnspan = 20)  
        
    
class PlaylistPage(tk.Frame):

    def __init__(self, parent, controller):
        
        self.controller = controller
        self.parent = parent        
        tk.Frame.__init__(self, parent)
        
        instr_label = tk.Label(self, text='Select a playlist!')
        instr_label.pack(padx=10, pady=10)          

    def populate(self):
        self.playlists = pc.get_playlists(self.controller.sess)
        for playlist in self.playlists:
            play_butt = tk.Button(self, text = playlist, command = lambda playlist=playlist: self.forward_artists(pc.select_playlist(self.playlists, playlist)))
            play_butt.pack()
            
        self.controller.canvas.create_window(0, 0, anchor=tk.NW, window=self.parent)

        self.parent.update_idletasks()
        
        self.controller.canvas.config(scrollregion=self.controller.canvas.bbox("all"))    
            
    def forward_artists(self, playlist):
        
        self.controller.artists = pc.get_artists(playlist)
        self.controller.artists_df = pd.DataFrame(np.array(self.controller.artists).T, columns=['artist_name'])
        
        for widget in self.controller.frames[ArtistsPage].winfo_children():
            widget.destroy()
        
        self.controller.frames[ArtistsPage].make_buttons()
        self.controller.frames[ArtistsPage].populate(self.controller.artists)
        self.controller.last_page = PlaylistPage
        self.controller.show_frame(ArtistsPage)
            
    
class StartPage(tk.Frame):
    
    def __init__(self, parent, controller):
        
        self.controller = controller
        self.parent = parent
        tk.Frame.__init__(self, parent)
        
        user_label = tk.Label(self, text="Spotify Username")
        passw_label = tk.Label(self, text="Password")
        user_box = tk.Entry(self, width = 20)
        passw_box = tk.Entry(self, width = 20, show='*')
        
        user_box.bind('<Return>', lambda x: self.login(user_box.get(), passw_box.get()))
        passw_box.bind('<Return>', lambda x: self.login(user_box.get(), passw_box.get()))
        
        user_label.grid(row=0)
        passw_label.grid(row=1)
        user_box.grid(row=0, column=1)
        passw_box.grid(row=1, column=1)
        
        login_butt = tk.Button(self, text='Login', command = lambda: self.login(user_box.get(), passw_box.get()))
        exit_butt = tk.Button(self, text='Exit', command=self.quit)
        
        login_butt.grid(row=2)
        exit_butt.grid(row=2, column=1)
        
        instr1_label = tk.Label(self, text='Or...')
        instr2_label = tk.Label(self, text='Type a list of artists separated by a comma.')        

        blank = tk.Frame(self, height=50) 
        blank.grid(row=3)
        
        instr1_label.grid(row=4, columnspan=2)
        instr2_label.grid(row=5, columnspan=2)
        
        artists_label = tk.Label(self, text='Artists')
        artists_box = tk.Entry(self, width=20)
        
        artists_box.bind('<Return>', lambda x: self.forward_artists(artists_box.get()))
        
        artists_label.grid(row=6, column=0)
        artists_box.grid(row=6,column=1)
        
        enter_butt = tk.Button(self, text='Enter', command = lambda: self.forward_artists(artists_box.get()))
        clear_butt = tk.Button(self, text='Clear', command = lambda: artists_box.delete(0, 'end'))

        enter_butt.grid(row=8)
        clear_butt.grid(row=8, column=1)        
        
    def login(self, user, passw):
        
        if not self.controller.loggedin:
            self.controller.sess = pc.login_spotify(user, passw, './')
            self.controller.frames[PlaylistPage].populate()
            self.controller.loggedin = True
        
        self.controller.last_page = StartPage
        self.controller.show_frame(PlaylistPage)
        
    def forward_artists(self, artists):
        print 'forwards!'
        
        self.controller.last_page = StartPage
    
    
class SpotifyConcert(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Hot Relevant Concerts in Your Area!")
        self.focus_force()
        
        self.geometry('1200x800')
        
        menu = tk.Menu(self)
        self.config(menu=menu)
        sub_menu = tk.Menu(menu)
        menu.add_cascade(label='File', menu=sub_menu)
        sub_menu.add_command(label='Home', command=self.go_home)
        sub_menu.add_command(label='Exit', command=self.quit)        
        
        vscrollbar = AutoScrollbar(self)
        vscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        hscrollbar = AutoScrollbar(self, orient=tk.HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky=tk.E+tk.W)
        
        canvas = tk.Canvas(self,
                        yscrollcommand=vscrollbar.set,
                        xscrollcommand=hscrollbar.set)
        canvas.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        
        vscrollbar.config(command=canvas.yview)
        hscrollbar.config(command=canvas.xview)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)        
        
        container = tk.Frame(canvas)
        
        container.pack(side='top', fill='both', expand=True)
        
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(1, weight=1)
        
        self.canvas = canvas
        
        self.frames = {}

        for F in [StartPage, PlaylistPage, ArtistsPage, SimilarArtistsPage, ConcertLinksPage]:

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)
        
        self.last_page = StartPage
        self.sess = None        
        self.artists = []
        self.similar_artists = None
        self.artists_df = None
        self.loggedin = False
        self.links = None
        self.metro_df = []
        self.joined_df = []
        

    def show_frame(self, cont):
    
        frame = self.frames[cont]
        frame.tkraise()
    
    def go_home(self):
        self.show_frame(StartPage)
        
if __name__ == '__main__':
    if not os.path.exists('./tmp'):
        os.mkdir('./tmp')
    app = SpotifyConcert()
    app.mainloop()