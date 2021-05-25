import React from "react";
import { INode } from "./interfaces";

import "./styles/_dnd-sidebar.scss";

const NODES = JSON.parse(document.getElementById("nodes").textContent) as INode;

const SECTIONS = Object.keys(NODES).reduce((sections, key) => {
  const node = NODES[key];
  const section = node.section;
  if (!sections[section]) {
    sections[section] = [key];
  } else {
    sections[section] = [...sections[section], key];
  }
  return sections;
}, {});
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

      {Object.keys(SECTIONS).map((section) => (
        <div className="flex flex-col" key={section}>
          <span className="font-semibold text-lg">{section}</span>
          {SECTIONS[section].map((kind) => {
            const node = NODES[kind];

            return (
              <div
                key={kind}
                className="dnd-sidebar__node "
                onDragStart={(event) => onDragStart(event, kind)}
                draggable
              >
                <i className={`dnd-sidebar__icon fad ${node.icon}`}></i>
                <div className="flex flex-col">
                  <span className="dnd-sidebar__name">{node.displayName}</span>
                  <span className="dnd-sidebar__description">
                    {node.description}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ))}
    </aside>
  );
};
