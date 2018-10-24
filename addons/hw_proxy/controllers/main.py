from odoo import http

# drivers modules must add to drivers an object with a get_status() method
# so that 'status' can return the status of all active drivers
drivers = {}


class Proxy(http.Controller):

    def get_status(self):
        statuses = {}
        for driver in drivers:
            statuses[driver] = drivers[driver].get_status()
        return statuses

    @http.route('/hw_proxy/hello')
    def hello(self):
        return "ping"
