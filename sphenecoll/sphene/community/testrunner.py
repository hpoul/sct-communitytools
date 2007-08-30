
import unittest
from django.conf import settings
from django.test.utils import setup_test_environment, teardown_test_environment
from django.test.utils import create_test_db, destroy_test_db
from django.test.testcases import OutputChecker, DocTestRunner
from django.db.models import get_app, get_apps
import os
from sphene.contrib.libs.codecoverage import coverage, coverage_color

from django.test.simple import get_tests, build_suite

def run_tests(test_labels, verbosity = 1, interactive = True, extra_tests=[]):
    """
    This is basically a copy of the default django run_tests method, except
    with the addition of the coverage report as documented at
    http://siddhi.blogspot.com/2007/04/code-coverage-for-your-django-code.html
    """

    if hasattr(settings, 'TEST_DATABASE_ENGINE'):
        settings.DATABASE_ENGINE = settings.TEST_DATABASE_ENGINE

    setup_test_environment()
    
    settings.DEBUG = False    
    suite = unittest.TestSuite()
    
    if test_labels:
        for label in test_labels:
            if '.' in label:
                suite.addTest(build_test(label))
            else:
                app = get_app(label)
                suite.addTest(build_suite(app))
    else:
        for app in get_apps():
            suite.addTest(build_suite(app))
    
    for test in extra_tests:
        suite.addTest(test)

    old_name = settings.DATABASE_NAME
    create_test_db(verbosity, autoclobber=not interactive)

    coverage.start()
    print "Running tests ..."
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    print "Done running tests."
    coverage.stop()
    if not os.path.exists(settings.COVERAGE_DIR):
        os.makedirs(settings.COVERAGE_DIR)

    modules = []
    for module_string in settings.COVERAGE_MODULES:
        module = __import__(module_string, globals(), locals(), [""])
        modules.append(module)
        f,s,m,mf = coverage.analysis(module)
        fp = file(os.path.join(settings.COVERAGE_DIR, module_string + ".html"), "wb")
        coverage_color.colorize_file(f, outstream=fp, not_covered=mf)
        fp.close()
    coverage.report(modules)
    coverage.erase()
    
    destroy_test_db(old_name, verbosity)
    
    teardown_test_environment()
    
    return len(result.failures) + len(result.errors)


import unittest, difflib, pdb, tempfile



class _OutputRedirectingPdb(pdb.Pdb):
    """
    A specialized version of the python debugger that redirects stdout
    to a given stream when interacting with the user.  Stdout is *not*
    redirected when traced code is executed.
    """
    def __init__(self, out):
        self.__out = out
        self.__debugger_used = False
        pdb.Pdb.__init__(self)

    def set_trace(self):
        self.__debugger_used = True
        pdb.Pdb.set_trace(self)

    def set_continue(self):
        if self.__debugger_used:
            pdb.Pdb.set_continue(self)

    def trace_dispatch(self, *args):
        # Redirect stdout to the given stream.
        save_stdout = sys.stdout
        sys.stdout = self.__out
        # Call Pdb's trace dispatch method.
        try:
            return pdb.Pdb.trace_dispatch(self, *args)
        finally:
            sys.stdout = save_stdout

import django.test._doctest

django.test._doctest._OutputRedirectingPdb = _OutputRedirectingPdb
