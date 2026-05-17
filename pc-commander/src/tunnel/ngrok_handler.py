import subprocess
import requests
import time
import sys
import os


class NgrokHandler:
    def __init__(self, auth_token: str = None, port: int = 5000):
        self.auth_token = auth_token
        self.port = port
        self.public_url = None
        self.process = None

    def start(self) -> str:
        try:
            from pyngrok import ngrok, conf
            if self.auth_token:
                conf.get_default().auth_token = self.auth_token
                ngrok.set_auth_token(self.auth_token)

            tunnel = ngrok.connect(self.port, "http")
            self.public_url = tunnel.public_url.replace("http://", "https://")
            return self.public_url
        except Exception as e:
            return None

    def stop(self):
        try:
            from pyngrok import ngrok
            ngrok.kill()
            self.public_url = None
        except Exception:
            pass

    def get_url(self) -> str:
        return self.public_url

    def verify_token(self) -> bool:
        try:
            from pyngrok import ngrok, conf
            if self.auth_token:
                conf.get_default().auth_token = self.auth_token
            tunnel = ngrok.connect(9999, "http")
            ngrok.disconnect(tunnel.public_url)
            return True
        except Exception:
            return False
