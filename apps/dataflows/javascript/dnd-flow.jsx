import React, { useState, useRef, useEffect } from "react";
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  removeElements,
  Controls,
} from "react-flow-renderer";

import Sidebar from "./sidebar";

import "./dnd.css";

const DnDFlow = ({ client }) => {
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [elements, setElements] = useState([]);

  const onConnect = (params) => {
    const parents = elements
      .filter((el) => el.target === params.target)
      .map((el) => el.source);

    client.action(
      window.schema,
      ["dataflows", "api", "nodes", "partial_update"],
      {
        id: params.target,
        parents: [...parents, params.source],
      }
    );
    setElements((els) =>
      addEdge({ ...params, arrowHeadType: "arrowclosed" }, els)
    );
  };

  const dataflowId = window.location.pathname.split("/")[2];

  const onElementsRemove = (elementsToRemove) => {
    setElements((els) => removeElements(elementsToRemove, els));
    elementsToRemove.forEach((el) => {
      client.action(window.schema, ["dataflows", "api", "nodes", "delete"], {
        id: el.id,
      });
    });
  };

  const onLoad = (_reactFlowInstance) =>
    setReactFlowInstance(_reactFlowInstance);

  const onDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  const getPosition = (event) => {
    const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
    return reactFlowInstance.project({
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    });
  };

  const onDragStop = (event, node) => {
    const position = getPosition(event);

    client.action(
      window.schema,
      ["dataflows", "api", "nodes", "partial_update"],
      {
        id: node.id,
        x: position.x,
        y: position.y,
      }
    );
  };

  useEffect(() => {
    client
      .action(window.schema, ["dataflows", "api", "nodes", "list"])
      .then((result) => {
        const newElements = result.results.map((r) => ({
          id: `${r.id}`,
          type: "default",
          data: { label: r.kind },
          position: { x: r.x, y: r.y },
        }));

        const edges = result.results
          .filter((r) => r.parents.length)
          .reduce((acc, curr) => {
            return [
              ...acc,
              ...curr.parents.map((p) => ({
                id: `reactflow__edge-${p}null-${curr.id}null`,
                source: p.toString(),
                sourceHandle: null,
                targetHandle: null,
                arrowHeadType: "arrowclosed",
                target: curr.id.toString(),
              })),
            ];
          }, []);
        setElements((els) => els.concat([...newElements, ...edges]));
      });
  }, []);

  const onDrop = async (event) => {
    event.preventDefault();

    const type = event.dataTransfer.getData("application/reactflow");
    const position = getPosition(event);

    const result = await client.action(
      window.schema,
      ["dataflows", "api", "nodes", "create"],
      {
        kind: type,
        dataflow: dataflowId,
        x: position.x,
        y: position.y,
      }
    );

    const newNode = {
      id: `${result.id}`,
      type: ["input", "output"].includes(type) ? type : "default",
      data: { label: result.kind },
      position,
    };

    setElements((es) => es.concat(newNode));
  };

  return (
    <div className="dndflow">
      <ReactFlowProvider>
        <div className="reactflow-wrapper" ref={reactFlowWrapper}>
          <ReactFlow
            elements={elements}
            onConnect={onConnect}
            onElementsRemove={onElementsRemove}
            onLoad={onLoad}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeDragStop={onDragStop}
            onElementClick={(event, element) => {
              document.getElementById("dataflow-node").setAttribute(
                "src",
                // TODO: populate URL from django reverse
                `http://localhost:8000/dataflows/${dataflowId}/nodes/${element.id}`
              );
            }}
          >
            <Controls />
          </ReactFlow>
        </div>
        <Sidebar />
      </ReactFlowProvider>
    </div>
  );
};

export default DnDFlow;
