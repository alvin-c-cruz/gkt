from application import create_app, db
import socket, webbrowser


app = create_app()


if __name__ == "__main__":   
    app.config["FLASKENV"] = "development"
    app.debug=True
    
    host_name = hostname = socket.gethostname()
    host = socket.gethostbyname(host_name)
    port = 9000
    
    web_site = f"http://{host}:{port}"
    print(f"Please type on your browser this web address: {web_site}")
    print(host_name)
        
    # webbrowser.open(web_site)
    
    app.run(host="0.0.0.0", port=port)
