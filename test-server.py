#!/usr/bin/env python3
"""
Simple HTTP server for testing MMM-Trello test page with Trello API proxy
"""
import http.server
import socketserver
import webbrowser
import os
import sys
import urllib.parse
import urllib.request
import json

PORT = 8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight OPTIONS requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '3600')
    
    def end_headers(self):
        # Add CORS headers to allow API calls
        self.send_cors_headers()
        super().end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Proxy Trello API requests
        if parsed_path.path.startswith('/api/trello/'):
            self.handle_trello_proxy(parsed_path)
        # Proxy Trello member avatars to avoid CORS issues
        elif parsed_path.path.startswith('/api/avatar/'):
            self.handle_avatar_proxy(parsed_path)
        else:
            # Serve static files
            super().do_GET()
    
    def handle_trello_proxy(self, parsed_path):
        """Proxy requests to Trello API"""
        try:
            # Extract the Trello API path
            trello_path = parsed_path.path.replace('/api/trello', '')
            
            # Get query parameters
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # Build Trello API URL
            trello_url = f"https://api.trello.com{trello_path}"
            if query_params:
                # Reconstruct query string
                query_string = urllib.parse.urlencode(query_params, doseq=True)
                trello_url += f"?{query_string}"
            
            # Make request to Trello API
            req = urllib.request.Request(trello_url)
            with urllib.request.urlopen(req) as response:
                data = response.read()
                status_code = response.getcode()
                
                # Send response back to client
                self.send_response(status_code)
                self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(data)
                
        except urllib.error.HTTPError as e:
            error_data = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(error_data)
        except Exception as e:
            error_response = json.dumps({
                'error': str(e)
            }).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(error_response)
    
    def handle_avatar_proxy(self, parsed_path):
        """Proxy requests to Trello member avatars"""
        try:
            # Extract the avatar path (everything after /api/avatar/)
            avatar_path = parsed_path.path.replace('/api/avatar/', '')
            
            # Build Trello avatar URL
            avatar_url = f"https://trello-members.s3.amazonaws.com/{avatar_path}"
            
            # Make request to Trello avatar
            req = urllib.request.Request(avatar_url)
            with urllib.request.urlopen(req) as response:
                data = response.read()
                status_code = response.getcode()
                
                # Send response back to client
                self.send_response(status_code)
                content_type = response.headers.get('Content-Type', 'image/png')
                self.send_header('Content-Type', content_type)
                # Cache avatars for 1 hour
                self.send_header('Cache-Control', 'public, max-age=3600')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(data)
                
        except urllib.error.HTTPError as e:
            error_data = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'text/plain')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(error_data)
        except Exception as e:
            error_response = json.dumps({
                'error': str(e)
            }).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(error_response)

    def log_message(self, format, *args):
        # Custom log format
        sys.stderr.write("%s - - [%s] %s\n" %
                        (self.address_string(),
                         self.log_date_time_string(),
                         format % args))

def main():
    # Change to the directory where this script is located
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    Handler = MyHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Test server running at http://localhost:{PORT}/")
            print("Press Ctrl+C to stop the server")
            
            # Open browser automatically
            webbrowser.open(f'http://localhost:{PORT}/test.html')
            
            # Serve forever
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)
    except OSError as e:
        if e.errno == 98 or e.errno == 10048:  # Address already in use
            print(f"Port {PORT} is already in use. Please close the other server or change the PORT.")
        else:
            print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
