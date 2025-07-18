from comfyui import BaseNode

class CounterNode(BaseNode):
    def __init__(self):
        super().__init__()
        # Initialize the counter
        self.counter = 0
        # Add a string widget to display the counter value
        self.add_widget("string", "Counter Value", str(self.counter))

    def process(self):
        # Increment the counter
        self.counter += 1
        # Update the widget with the new counter value
        self.set_widget_value("Counter Value", str(self.counter))
        # Return the new counter value
        return self.counter

# Define the node class mappings
NODE_CLASS_MAPPINGS = {
    "CounterNode": CounterNode
}

# Define the node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "CounterNode": "Counter Node"
}
