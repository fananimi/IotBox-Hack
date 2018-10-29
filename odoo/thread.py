from bottle import Bottle
from odoo.http import EnableCorsPlugin, JSONRPCPlugin, Controller
from PyQt4.QtCore import QThread


class Thread(QThread):

    def lockedstart(self):
        if not self.isRunning():
            self.start()


class WebThread(Thread):

    def run(self):
        app = Bottle()

        def get_all_subclasses(cls):
            all_subclasses = []

            for subclass in cls.__subclasses__():
                all_subclasses.append(subclass)
                all_subclasses.extend(get_all_subclasses(subclass))

            return all_subclasses

        # register all controller
        controllers = get_all_subclasses(Controller)
        for controller in controllers:
            controller.register(app)

        app.install(EnableCorsPlugin())
        app.install(JSONRPCPlugin())
        app.run(host='localhost', port=8080, debug=False)
