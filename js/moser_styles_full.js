import { app } from "../scripts/app.js";
import { api } from "../scripts/api.js";

const updateWidget = async (widget, fromValue, toValue) => {
    try {
        console.log(`Updating ${widget.name} from ${fromValue} to ${toValue}`);
        widget.value = toValue;
        widget.callback(widget.value);
    } catch (error) {
        console.error("Error updating widget:", error);
    }
};

const calculateNextNumber = (mode, currentValue, min, max) => {
    let newValue;
    console.log(`calculateNextNumber called with mode: ${mode}, currentValue: ${currentValue}, min: ${min}, max: ${max}`);
    
    switch (mode) {
        case "Random":
            // Ensure we have valid min/max values
            if (min >= max) {
                console.warn(`Invalid range: min (${min}) >= max (${max}), using min as fallback`);
                newValue = min;
            } else {
                newValue = Math.floor(Math.random() * (max - min + 1)) + min;
            }
            console.log(`Random mode: Generating random number between ${min} and ${max}: ${newValue}`);
            return newValue;
        case "Increment":
            newValue = currentValue >= max ? min : currentValue + 1;
            console.log(`Increment mode: ${currentValue} ${currentValue >= max ? `>= ${max}, wrapping to ${min}` : `+ 1 = ${newValue}`}`);
            return newValue;
        case "Decrement":
            newValue = currentValue <= min ? max : currentValue - 1;
            console.log(`Decrement mode: ${currentValue} ${currentValue <= min ? `<= ${min}, wrapping to ${max}` : `- 1 = ${newValue}`}`);
            return newValue;
        default:
            console.log(`Manual mode: Keeping current value ${currentValue}`);
            return currentValue;
    }
};

const handleExecutionStart = async (node) => {
    console.log("=== TRIGGER: Node Execution ===");
    const widgets = {
        current: node.widgets.find(w => w.name === "previous_prompt"),
        next: node.widgets.find(w => w.name === "next_prompt"),
        mode: node.widgets.find(w => w.name === "mode"),
        min: node.widgets.find(w => w.name === "minimum"),
        max: node.widgets.find(w => w.name === "maximum")
    };
    
    if (!Object.values(widgets).every(w => w)) {
        console.log("Missing required widgets");
        return;
    }
    
    console.log(`Node executing with Next Prompt value: ${widgets.next.value}`);
    console.log("Updating current prompt");
    await updateWidget(widgets.current, widgets.current.value, widgets.next.value);

    if (widgets.mode.value !== "Manual") {
        console.log("Calculating next number");
        const newNext = calculateNextNumber(
            widgets.mode.value,
            widgets.current.value,
            widgets.min.value,
            widgets.max.value
        );
        await updateWidget(widgets.next, widgets.next.value, newNext);
    }
};

const handleModeChange = async (node, newMode) => {
    console.log("\n=== Processing Mode Change ===");
    console.log(`Mode changing to: ${newMode}`);
    const widgets = {
        current: node.widgets.find(w => w.name === "previous_prompt"),
        next: node.widgets.find(w => w.name === "next_prompt"),
        min: node.widgets.find(w => w.name === "minimum"),
        max: node.widgets.find(w => w.name === "maximum")
    };
    
    if (!Object.values(widgets).every(w => w)) {
        console.log("Error: Missing required widgets");
        return;
    }

    if (newMode === "Manual") {
        console.log("Manual mode selected - keeping Next Prompt value as is");
        return;
    }

    // Simply use the same calculation function that works in the event handler
    const newNext = calculateNextNumber(
        newMode,
        widgets.current.value,
        widgets.min.value,
        widgets.max.value
    );

    console.log(`Current Prompt: ${widgets.current.value} (unchanged)`);
    console.log(`Next Prompt changing to: ${newNext}`);
    await updateWidget(widgets.next, widgets.next.value, newNext);
};

app.registerExtension({
    name: "Moser.StylesFull",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "MoserStylesFull") {
            // Set up event listeners for node execution
            api.addEventListener("executing", (e) => {
                if (e.detail) {
                    const node = app.graph._nodes.find(n => 
                        n.type === "MoserStylesFull" && n.id === Number(e.detail)
                    );
                    if (node) {
                        console.log(`Moser Styles Full node (ID: ${e.detail}) has begun execution`);
                        // Use a shorter delay and add retry logic for better reliability
                        setTimeout(() => handleExecutionStart(node), 100);
                    }
                }
            });

            // Handle widget setup for both initial load and new nodes
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }
                setupModeWidget(this);
            };

            const originalOnConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                if (originalOnConfigure) {
                    originalOnConfigure.apply(this, arguments);
                }
                setupModeWidget(this);
            };

            function setupModeWidget(node) {
                const modeWidget = node.widgets.find(w => w.name === "mode");
                if (modeWidget && !modeWidget._moserStylesInitialized) {
                    const originalCallback = modeWidget.callback;
                    const originalComputeSize = modeWidget.computeSize;
                    
                    modeWidget.callback = (function(value) {
                        if (originalCallback) {
                            originalCallback.apply(this, arguments);
                        }
                        
                        setTimeout(() => {
                            console.log("=== TRIGGER: Mode Widget Change ===");
                            console.log(`Mode widget value changed to: ${value}`);
                            
                            if (this) {
                                console.log(`Found node with ID: ${this.id}`);
                                handleModeChange(this, value).then(() => {
                                    console.log("Mode change handler completed successfully");
                                }).catch(error => {
                                    console.error("Error in mode change handler:", error);
                                });
                            } else {
                                console.log("Could not find MoserStylesFull node");
                            }
                        }, 100);
                    }).bind(node);

                    modeWidget._moserStylesInitialized = true;
                }
            }
        }
    }
});
