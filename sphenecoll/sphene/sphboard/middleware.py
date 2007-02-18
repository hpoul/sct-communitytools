from django import http
from django.db import connection
import time

class PerformanceMiddleware(object):
    def process_request(self, request):
        self.started = time.time()
        return None

    def process_response(self, request, response):
        duration = time.time() - self.started
        #print "duration: " + duration.__str__()
        #print "queries: " + connection.queries.__str__()
        response.write("duration: " + duration.__str__() + " seconds<br/><br/>")
        sqltotal = 0.0
        for query in connection.queries:
            #response.write("SQL (" + query['time'] + "): " + query['sql'] + "<br/>")
            sqltotal += float(query['time'])
        response.write("sql (" + len(connection.queries).__str__() + ") - " + sqltotal.__str__())
        return response

