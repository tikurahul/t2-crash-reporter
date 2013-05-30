import webapp2
from common import common_request
from webapp2 import uri_for
import model
import logging
import simhash


class RootHandler(webapp2.RequestHandler):
    @common_request
    def get(self):
        self.add_parameter('title', 'T2 Crash Detector')
        self.add_breadcrumb('Home', uri_for('home'))
        brand = model.Link('T2 Crash Detector', uri_for('home'))
        nav_links = []
        nav_links.append(model.Link('About', '#'))
        nav_links.append(model.Link('Contact', '#'))
        self.add_parameter('brand', brand)
        self.add_parameter('nav_links', nav_links)
        directory_links = []
        directory_links.append(model.Link('Submit Crash', uri_for('submit_crash')))
        self.add_parameter('directory_links', directory_links)
        self.render('index.html')


class SubmitCrashHandler(webapp2.RequestHandler):

    def _common(self, request):
        request.add_parameter('title', 'Submit Crash Report')
        request.add_breadcrumb('Home', uri_for('home'))
        request.add_breadcrumb('Submit Crash', uri_for('submit_crash'))
        brand = model.Link('T2 Crash Detector', uri_for('home'))
        nav_links = []
        nav_links.append(model.Link('About', '#'))
        nav_links.append(model.Link('Contact', '#'))
        request.add_parameter('brand', brand)
        request.add_parameter('nav_links', nav_links)

    @common_request
    def get(self):
        self.request_handler._common(self)
        self.render('submit-crash.html')

    @common_request
    def post(self):
        self.request_handler._common(self)
        if self.empty_query_string('crash'):
            self.request_handler.redirect(uri_for('submit_crash'))
        else:
            crash = self.get_parameter('crash')
            fingerprint = simhash.sim_hash(crash)
            message = 'Submitting crash report with fingerprint %s' % (fingerprint)
            logging.info(message)
            self.add_message(message)
            self.render('submit-crash.html')


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/', handler='main.RootHandler', name='home'),
        webapp2.Route('/crashes/submit', handler='main.SubmitCrashHandler', name='submit_crash'),
    ]
    ,debug=True
)