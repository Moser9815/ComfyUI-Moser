import { app } from "../scripts/app.js";
import { api } from "../scripts/api.js";

class MoserStylesService extends EventTarget {
    constructor(api) {
        super();
        
        // Track execution state
        this.currentExecution = null;
        this.executedNodeIds = [];
        this.moserStylesNodeIds = new Set();

        api.addEventListener("execution_start", (e) => {
            console.log("Execution started:", e.detail);
            const graph = app.graph;
            this.moserStylesNodeIds.clear();
            for (const node of graph._nodes) {
                if (node.type === "MoserStylesFull") {
                    this.moserStylesNodeIds.add(node.id);
                    console.log("Found MoserStylesFull node with ID:", node.id);
                }
            }
            this.executedNodeIds = [];
        });

        api.addEventListener("executing", (e) => {
            console.log("Currently executing:", e.detail);
            if (e.detail && this.moserStylesNodeIds.has(Number(e.detail))) {
                console.log("Moser Styles Full is being executed");
            }
            if (e.detail) {
                this.currentExecution = e.detail;
            } else {
                this.currentExecution = null;
            }
        });

        api.addEventListener("progress", (e) => {
            console.log("Progress update:", e.detail);
        });

        api.addEventListener("execution_cached", (e) => {
            console.log("Execution cached:", e.detail);
            if (e.detail.nodes) {
                this.executedNodeIds.push(...e.detail.nodes);
            }
        });

        api.addEventListener("executed", (e) => {
            console.log("Node executed:", e.detail);
            if (e.detail.node && this.moserStylesNodeIds.has(Number(e.detail.node))) {
                console.log("Moser Styles Full is completed");
            }
            if (e.detail.node) {
                this.executedNodeIds.push(e.detail.node);
            }
        });

        api.addEventListener("execution_error", (e) => {
            console.log("Execution error:", e.detail);
        });
    }
}

const SERVICE = new MoserStylesService(api);

app.registerExtension({
    name: "Moser.StylesFull",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "MoserStylesFull") {
            const nodeStates = new Map();
            
            // Add event listener directly to api
            api.addEventListener("executed", (e) => {
                console.log("Execution completed with details:", e.detail);
            });

            const updateWidget = async (widget, value, maxRetries = 3) => {
                let retries = 0;
                const tryUpdate = () => {
                    try {
                        widget.value = value;
                        widget.callback(widget.value);
                        return true;
                    } catch (error) {
                        console.error("Error updating widget:", error);
                        return false;
                    }
                };

                while (retries < maxRetries) {
                    if (tryUpdate()) {
                        console.log("Widget value updated to:", value);
                        return true;
                    }
                    retries++;
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                return false;
            };
            
            const calculateNextNumber = (data, mode) => {
                const min = data.last_min;
                const max = data.last_max;
                const current = data.current_number;

                switch (mode) {
                    case "Manual":
                        return current;
                    case "Random":
                        return Math.floor(Math.random() * (max - min + 1)) + min;
                    case "Increment":
                        return current >= max ? min : current + 1;
                    case "Decrement":
                        return current <= min ? max : current - 1;
                    default:
                        return current;
                }
            };

            const checkJsonAndUpdateWidget = async (node) => {
                try {
                    const response = await fetch(`/moser_styles_full_data.json?t=${Date.now()}`);
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    
                    const data = await response.json();
                    const widget = node.widgets.find(w => w.name === "manual_number");
                    const modeWidget = node.widgets.find(w => w.name === "selection_mode");
                    if (!widget || !modeWidget) return;

                    const nextNumber = calculateNextNumber(data, modeWidget.value);
                    
                    if (widget.value !== nextNumber) {
                        console.log("Numbers don't match - Widget:", widget.value, "Next Number:", nextNumber);
                        await updateWidget(widget, nextNumber);
                    }

                    nodeStates.set(node.id, {
                        lastNumber: nextNumber,
                        lastMode: modeWidget.value,
                        lastUpdate: Date.now()
                    });
                    
                } catch (error) {
                    console.error("Error checking JSON file:", error);
                }
            };

            // Override the onExecuted method
            const originalOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                console.log("Node has been run");
                if (originalOnExecuted) {
                    originalOnExecuted.apply(this, arguments);
                }
                setTimeout(() => checkJsonAndUpdateWidget(this), 200);
            };

            // Add widget change handler
            const originalOnConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                if (originalOnConfigure) {
                    originalOnConfigure.apply(this, arguments);
                }

                // Find the selection_mode widget and add change handler
                const modeWidget = this.widgets.find(w => w.name === "selection_mode");
                if (modeWidget) {
                    const originalCallback = modeWidget.callback;
                    modeWidget.callback = function(value) {
                        if (originalCallback) {
                            originalCallback.apply(this, arguments);
                        }
                        // Update the preview when mode changes
                        checkJsonAndUpdateWidget(this.node);
                    };
                }
            };

            // Set up periodic checking (every 2 seconds)
            setInterval(() => {
                const nodes = app.graph._nodes.filter(n => n.type === "MoserStylesFull");
                nodes.forEach(node => checkJsonAndUpdateWidget(node));
            }, 2000);
        }
    }
});
