from .meme import handler as meme
from http.server import HTTPServer


def main():
    server = HTTPServer(('localhost', 8080), meme)
    print('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()


if __name__ == '__main__':
    main()
