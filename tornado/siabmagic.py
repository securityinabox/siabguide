#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# WindyServer is the service exposing HTTP API to query TrackMap project

import tornado.ioloop
import tornado.web
from tornado.util import bytes_type, unicode_type
from tornado import escape
import sys
import os
from termcolor import colored
import logging

LOGFILE='/home/publisher/publisher.log'

ACAO = None

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("visualisation/index.html")


class WindyHandler(tornado.web.RequestHandler):

    counter = 0
    tracker = {}
    index = 0

    def write(self, chunk):
        """
        This is exactly a copy of the original Tornado RequestHandler.write,
        but here I'm supporting also the list as JSON
        """
        if ACAO:
            self.set_header('Access-Control-Allow-Origin', "%s" % ACAO)

        print WindyHandler.counter, self.request.uri

        WindyHandler.counter += 1
        WindyHandler.tracker.setdefault(self.request.remote_ip, []).append(self.request.uri)

        if (WindyHandler.counter % 300) == 0:
            import json
            with file(os.path.join("/tmp", "log-%d.log" % WindyHandler.index), 'w+') as xx:
                json.dump(WindyHandler.tracker, xx)

            WindyHandler.index += 1

        if self._finished:
            raise RuntimeError("Cannot write() after finish().  May be caused "
                               "by using async operations without the "
                               "@asynchronous decorator.")
        if not isinstance(chunk, (bytes_type, unicode_type, dict, list)):
            raise TypeError("write() only accepts bytes, unicode, and dict objects")
        if isinstance(chunk, (dict, list) ):
            chunk = escape.json_encode(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        chunk = escape.utf8(chunk)
        self._write_buffer.append(chunk)

class TestSIAB(WindyHandler):

    def get(self, reqchapt):

        excluded = ['tornado', 'README', '.git', 'template']

        siabh = '/home/qq/Dev/siab-content/'

        total_ret = []
        for siabdir in os.listdir(siabh):
            if siabdir in excluded:
                continue

            chapter = os.path.join(siabh, siabdir)
            files = os.listdir(chapter)

            ret = dict({ 'chapter': chapter, 'files' : []})
            for f in files:
                filepath = os.path.join(chapter, f)
                filedict = dict({ 'file':filepath, 'keyword': {} })
                with open(os.path.join(chapter, f), 'r') as fp:
                    sectionlin = fp.readlines()

                    for i, lin in enumerate(sectionlin):
                        if lin == '\n':
                            print f, "end at", i
                            break

                        keyword, content = lin.split(':', 1)
                        filedict['keyword'].update({keyword: content})

                ret['files'].append(dict(filedict))
            total_ret.append(ret)

        self.finish(total_ret)



if __name__ == "__main__":

    apiMap = [
        # public API
        (r"/tutte/(.*)", TestSIAB),
        # index.html
        (r"/", IndexHandler),
        # last: wildcard!
        (r"/(.*)", tornado.web.StaticFileHandler,
         {"path": 'visualisation/'}),
    ]

    print colored("WindyServer Started!", 'green', 'on_white')

    try:
        application = tornado.web.Application(apiMap, debug=True)
        application.listen(8000)
    except Exception as xxx:
        print "Unable to bind port 8000: %s" % xxx
        logging.warn("Unable to bind port 8000: %s" % xxx)
        quit(-1)

    tornado.ioloop.IOLoop.instance().start()

