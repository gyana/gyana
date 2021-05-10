import React from "react";

const NODES = JSON.parse(document.getElementById("nodes").textContent);

export default () => {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <aside>
      <div className="description">
        You can drag these nodes to the pane on the left.
      </div>
      {NODES.map(({ value, label }) => (
        <div
          key={value}
          className="dndnode"
          onDragStart={(event) => onDragStart(event, value)}
          draggable
        >
          {label}
        </div>
      ))}
    </aside>
  );
};
