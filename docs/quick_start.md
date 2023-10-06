## XMLRPC
``` python
# Example usage
server = OpenUR.XMLRPC(port=33003) # Default port is 33000

# Define a custom function
def custom_function(arg1, arg2):
    return arg1 + arg2

# Register the custom function to the server
server.register_my_function(custom_function)

# Start the server (assuming you have a start() method)
server.start()
```