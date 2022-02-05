from app import create_app,db, socketInstance
from app.models import User
# from gevent.pywsgi import WSGIServer
# from tornado.httpserver import HTTPServer
# from tornado.wsgi import WSGIContainer
# from tornado.ioloop import IOLoop
import eventlet
from eventlet import wsgi




app=create_app()
@app.shell_context_processor
def make_shell_context():
    return {'db':db,'User':User}

# http_server = WSGIServer(('0.0.0.0', 5000), app)
# http_server.serve_forever()
if __name__ == '__main__':
    eventlet.monkey_patch()
    # serve(app, host='0.0.0.0', port=5000)
    #app.run(host='0.0.0.0', port='5000', debug=True,use_debugger=False, use_reloader=False, passthrough_errors=True) 
    # s = HTTPServer(WSGIContainer(app))
    # s.listen(5000)  # 监听5000 端口
    # IOLoop.current().start()
    # wsgi.server(eventlet.listen(("", 5000), app))
    socketInstance.run(app,  port = '5000', debug = True)