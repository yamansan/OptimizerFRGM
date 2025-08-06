#!/usr/bin/env python
"""
Simple HTTP Server for HTML Files
Serves files from Z:/Yaman directory to enable JavaScript fetch requests.
"""

import http.server
import socketserver
import os
import sys

def serve_html_files():
    """Serve HTML files from Z:/Yaman directory."""
    
    # Change to the Z:/Yaman directory
    os.chdir("Z:/Yaman")
    
    # Create server
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: Z:/Yaman")
        print(f"🔗 Open: http://localhost:{PORT}/risk_vs_price.html")
        print("Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    serve_html_files() 