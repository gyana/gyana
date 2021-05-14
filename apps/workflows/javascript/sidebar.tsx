import React from "react";

import "./styles/_dnd-sidebar.scss";

const NODES = JSON.parse(document.getElementById("nodes").textContent);

export default () => {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <aside className="dnd-sidebar">
      <p>You can drag these nodes to the pane on the left.</p>

      {NODES.map(({ value, label }) => (
        <div
          key={value}
          className="dnd-sidebar__node button button--sm button--tertiary"
          onDragStart={(event) => onDragStart(event, value)}
          draggable
        >
          {label}
        </div>
      ))}
    </aside>
  );
};
