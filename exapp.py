# test sanic server

from sanic import *

app = Sanic(__name__)
@app.route("/")
async def test(request):
    return "test"

if __name__ == '__main__':
    app.run()