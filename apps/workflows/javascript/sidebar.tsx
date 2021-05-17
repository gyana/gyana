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
      <hgroup>
        <h2>Nodes</h2>
        <p>You can drag these onto the pane on your left.</p>
      </hgroup>

      {NODES.map(({ value, label }) => (
        <div
          key={value}
          className="dnd-sidebar__node button button--sm button--square button--tertiary"
          onDragStart={(event) => onDragStart(event, value)}
          draggable
        >
          {label}
        </div>
      ))}
    </aside>
  );
};
