import time
from odoo import http
from odoo.thread import Thread
import addons.hw_proxy.controllers.main as hw_proxy


class EscposDriver(Thread):

    def run(self):
        print "running"
        a = 1
        while True:
            print "EscposDriver :: %s" % a
            a += 1
            time.sleep(1)

    def hai(self):
        print "hai"
        self.lockedstart()


driver = EscposDriver()
hw_proxy.drivers['escpos'] = driver


class HwEscpos(http.Controller):

    @http.route('/hw_proxy/hello')
    def hello(self):
        driver.hai()
        return "Hello !"
