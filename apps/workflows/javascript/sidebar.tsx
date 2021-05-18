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

      {Object.keys(NODES).map((key) => {
        const node = NODES[key];
        return (
          <div
            key={key}
            className="dnd-sidebar__node "
            onDragStart={(event) => onDragStart(event, key)}
            draggable
          >
            <i className={`icon fad ${node.icon}`}></i>
            <div className="flex flex-col">
              <span className="name">{node.displayName}</span>
              <span className="description">{node.description}</span>
            </div>
          </div>
        );
      })}
    </aside>
  );
};
