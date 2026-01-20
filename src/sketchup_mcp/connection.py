"""SketchUp TCP Connection Management"""

import socket
import json
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

from .config import config

logger = logging.getLogger("SketchupMCPServer")


@dataclass
class SketchupConnection:
    """Manages TCP connection to SketchUp extension"""

    host: str = "localhost"
    port: int = 9876
    sock: Optional[socket.socket] = None

    def connect(self) -> bool:
        """Connect to the SketchUp extension socket server"""
        if self.sock:
            try:
                self.sock.settimeout(0.1)
                self.sock.send(b'')
                return True
            except (socket.error, BrokenPipeError, ConnectionResetError):
                logger.info("Connection test failed, reconnecting...")
                self.disconnect()

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to SketchUp at {self.host}:{self.port}")

            # Send authentication if secret is configured
            if config.auth_secret:
                auth_msg = json.dumps({"secret": config.auth_secret}) + "\n"
                self.sock.sendall(auth_msg.encode('utf-8'))
                logger.debug("Sent authentication")

            return True
        except Exception as e:
            logger.error(f"Failed to connect to SketchUp: {str(e)}")
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
            self.sock = None
            return False

    def disconnect(self):
        """Disconnect from the SketchUp extension"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")
            finally:
                self.sock = None

    def _receive_full_response(self, buffer_size: int = 8192) -> bytes:
        """Receive complete JSON response, potentially in multiple chunks"""
        chunks = []
        self.sock.settimeout(15.0)

        try:
            while True:
                try:
                    chunk = self.sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving data")
                        break

                    chunks.append(chunk)

                    # Try to parse as JSON to check if complete
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        return data
                    except json.JSONDecodeError:
                        continue

                except socket.timeout:
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    raise Exception(f"Connection error: {str(e)}")

        except socket.timeout:
            pass

        if chunks:
            data = b''.join(chunks)
            try:
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response")
        else:
            raise Exception("No data received")

    def send_command(
        self,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        request_id: Any = None
    ) -> Dict[str, Any]:
        """Send a tool command to SketchUp and return the response"""
        if not self.connect():
            raise ConnectionError(
                "Could not connect to SketchUp. "
                "Make sure SketchUp is running and the MCP extension is started "
                "(Plugins → MCP Server → Start Server)"
            )

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            },
            "id": request_id
        }

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                request_bytes = json.dumps(request).encode('utf-8') + b'\n'
                self.sock.sendall(request_bytes)

                response_data = self._receive_full_response()
                response = json.loads(response_data.decode('utf-8'))

                if "error" in response:
                    error_msg = response["error"].get("message", "Unknown error")
                    raise Exception(f"SketchUp error: {error_msg}")

                return response.get("result", {})

            except (socket.timeout, ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                if attempt < max_retries:
                    logger.warning(f"Connection error (attempt {attempt + 1}): {str(e)}")
                    self.disconnect()
                    if not self.connect():
                        break
                else:
                    self.sock = None
                    raise Exception(f"Connection lost after {max_retries + 1} attempts")

            except json.JSONDecodeError as e:
                raise Exception(f"Invalid response from SketchUp: {str(e)}")

        # If we exit the loop without returning, reconnection failed
        raise ConnectionError("Failed to reconnect to SketchUp after connection loss")


def parse_tool_response(result: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Extract success status and text from standard tool response.

    Args:
        result: Response dict from send_command()

    Returns:
        Tuple of (success: bool, text: str)
    """
    content = result.get("content", [])
    if isinstance(content, list) and content:
        text = content[0].get("text", "")
        is_error = result.get("isError", False)
        return (not is_error, text)
    return (False, "No response from SketchUp")


# Global connection instance
# TODO Phase 2: Refactor to dependency injection via FastMCP context
_connection: Optional[SketchupConnection] = None


def get_connection() -> SketchupConnection:
    """Get or create the global SketchUp connection"""
    global _connection

    if _connection is None:
        _connection = SketchupConnection()

    return _connection


def close_connection():
    """Close the global connection"""
    global _connection

    if _connection:
        _connection.disconnect()
        _connection = None
