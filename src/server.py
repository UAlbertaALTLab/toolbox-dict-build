import http.server
import socketserver
import io
from multipart import parse_options_header, MultipartParser
from latex import LatexBuildError
from latex.build import PdfLatexBuilder
from parse import load_toolbox
from entries import make_dictionary

class ArokHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        with open("index.html", "rb") as f:
            self.wfile.write(f.read())

    def do_POST(self):
        print("post requested.")
        length = int(self.headers.get('content-length', "0"))
        data = self.rfile.read(length)
        content_type, options = parse_options_header(self.headers.get('content-type'))
        toolbox = None
        if content_type == "multipart/form-data" and 'boundary' in options:
            boundary = options["boundary"]
            parser = MultipartParser(io.BytesIO(data), boundary)

            for part in parser: 
                if part and part.filename and part.name == 'toolbox':
                    toolbox = part.value
            # Free up resources after use
            for part in parser.parts():
                if part:
                    part.close()
            if toolbox:
                try:
                    dict_file = make_dictionary(load_toolbox(toolbox))
                    print("Dictionary made. building...")
                except ValueError as e:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write("Your toolbox file has some formatting issues.  This is the error we detected:\n\n\n".encode("utf-8"))
                    self.wfile.write("{}\n\n".format(str(e)).encode("utf-8"))
                    return
                try:
                    builder = PdfLatexBuilder(pdflatex="pdflatex")
                    latex = dict_file.latex()
                    #with open ("dict.tex", "w") as f:
                    #    f.write(latex)
                    pdf = builder.build_pdf(latex) 
                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf; charset=utf-8")
                    self.send_header("Content-Disposition", "inline; filename=\"dictionary.pdf\"")
                    self.end_headers()
                    self.wfile.write(bytes(pdf))
                    return
                except LatexBuildError as e:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write("There were issues on the file. Send a copy to altlab of the input files.\n\n\n".encode("utf-8"))
                    for err in e.get_errors():
                        self.wfile.write("{}\n\n".format(err["error"]).encode("utf-8"))
                    return
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write("You didn't send a toolbox file.".encode("utf-8"))
    
PORT = 8000

with socketserver.TCPServer(("", PORT), ArokHandler) as httpd:
    print("serving at port ", PORT)
    httpd.serve_forever()