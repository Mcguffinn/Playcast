# import os
# import logging
# import json
# from flask import Flask, render_template, Response
# from tornado.wsgi import WSGIContainer
# from tornado.httpserver import HTTPServer
# from tornado.ioloop import IOLoop




# def return_music_dict():
#     d = []
#     id_counter = 0
#     for filename in os.listdir('F:\Music'):
#         if filename.endswith('.mp3'):
#             id_counter += 1
#             d.append(
#                 { 'id' : id_counter, 'name' : filename.replace('.mp3',''), 'link' : 'F:\Music' + filename })
#     return d


# @route('/')
# def show_music():
#     general_data = {
#         'title': 'Music Player'
#     }
#     stream_entries = return_music_dict()
#     return render_template('index.html', entries=stream_entries, **general_data)


