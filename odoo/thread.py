from odoo.http import HTTPServer, EnableCorsPlugin, JSONRPCPlugin, Controller
from PyQt4.QtCore import QThread

from config import Config


class Thread(QThread):
    def isAlive(self):
        return self.isRunning()

    def lockedstart(self):
        if not self.isAlive():
            self.start()


class WebThread(Thread):

    def run(self):
        app = HTTPServer()

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
        port = Config.getInstance().get_service_port()
        app.run(host='localhost', port=port, debug=False)
