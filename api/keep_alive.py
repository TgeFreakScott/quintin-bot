from flask import Flask, Response

app = Flask(__name__)

@app.route('/')
def index():
    return Response("Quintin is alive, stew's on.", mimetype='text/plain')

# Required for Vercel
def handler(request):
    return app(request.environ, lambda status, headers: (status, headers, []))
