import React, { useState, useRef, useEffect } from "react";
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  removeElements,
  Controls,
  Handle,
  NodeProps,
  Position,
} from "react-flow-renderer";

import Sidebar from "./sidebar";

import { addParam } from "./util";
import "./styles/_dnd-flow.scss";
import "./styles/_react-flow.scss";

const DnDFlow = ({ client }) => {
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [elements, setElements] = useState([]);

  const workflowId = window.location.pathname.split("/")[4];

  const onConnect = (params) => {
    const parents = elements
      .filter((el) => el.target === params.target)
      .map((el) => el.source);

    client.action(
      window.schema,
      ["workflows", "api", "nodes", "partial_update"],
      {
        id: params.target,
        parents: [...parents, params.source],
      }
    );
    setElements((els) => addEdge({ ...params, arrowHeadType: "arrow" }, els));
  };

  const onElementsRemove = (elementsToRemove) => {
    setElements((els) => removeElements(elementsToRemove, els));
    elementsToRemove.forEach((el) => {
      client.action(window.schema, ["workflows", "api", "nodes", "delete"], {
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
      ["workflows", "api", "nodes", "partial_update"],
      {
        id: node.id,
        x: position.x,
        y: position.y,
      }
    );
  };

  useEffect(() => {
    client
      .action(window.schema, ["workflows", "api", "nodes", "list"], {
        workflow: workflowId,
      })
      .then((result) => {
        const newElements = result.results.map((r) => ({
          id: `${r.id}`,
          type: ["input", "output"].includes(r.kind) ? r.kind : "default",
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
                type: "smoothstep",
                targetHandle: null,
                arrowHeadType: "arrow",
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
      ["workflows", "api", "nodes", "create"],
      {
        kind: type,
        workflow: workflowId,
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
            nodeTypes={defaultNodeTypes}
            elements={elements}
            onConnect={onConnect}
            onElementsRemove={onElementsRemove}
            onLoad={onLoad}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeDragStop={onDragStop}
          >
            <Controls />
          </ReactFlow>
        </div>
        <Sidebar />
      </ReactFlowProvider>
    </div>
  );
};

const OpenButton = ({ id }) => {
  const workflowId = window.location.pathname.split("/")[4];

  return (
    <button
      className="absolute -bottom-8"
      data-src={`/workflows/${workflowId}/nodes/${id}`}
      data-controller="url-search-params"
      data-url-search-params-key-value="node_id"
      data-url-search-params-val-value={id}
      data-action="click->tf-modal#open click->url-search-params#add"
    >
      Open
    </button>
  );
};

const InputNode = ({ id, data, isConnectable, selected }: NodeProps) => (
  <>
    {selected && <OpenButton id={id} />}
    {data.label}
    <Handle
      type="source"
      position={Position.Right}
      isConnectable={isConnectable}
    />
  </>
);

const OutputNode = ({ id, data, isConnectable, selected }: NodeProps) => (
  <>
    {selected && <OpenButton id={id} />}
    <Handle
      type="target"
      position={Position.Left}
      isConnectable={isConnectable}
    />
    {data.label}
  </>
);

const DefaultNode = ({
  id,
  data,
  isConnectable,
  targetPosition = Position.Left,
  sourcePosition = Position.Right,
  selected,
}: NodeProps) => (
  <>
    {selected && <OpenButton id={id} />}
    <Handle
      type="target"
      position={targetPosition}
      isConnectable={isConnectable}
    />
    {data.label}
    <Handle
      type="source"
      position={sourcePosition}
      isConnectable={isConnectable}
    />
  </>
);

const defaultNodeTypes = {
  input: InputNode,
  output: OutputNode,
  default: DefaultNode,
};

export default DnDFlow;
