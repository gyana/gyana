import React, {
  useState,
  useRef,
  useEffect,
  createContext,
  useContext,
} from "react";
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  removeElements,
  Controls,
  Handle,
  NodeProps,
  Position,
  updateEdge,
  isNode,
  Edge,
  Node,
  isEdge,
} from "react-flow-renderer";

import Sidebar from "./sidebar";

import "./styles/_dnd-flow.scss";
import "./styles/_react-flow.scss";

const DnDFlow = ({ client }) => {
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [elements, setElements] = useState<(Edge | Node)[]>([]);

  // TODO: Make more robust to url changes
  const workflowId = window.location.pathname.split("/")[4];

  const updateParents = (id: string, parents: string[]) =>
    client.action(
      window.schema,
      ["workflows", "api", "nodes", "partial_update"],
      {
        id,
        parents,
      }
    );

  const onConnect = (params) => {
    const parents = elements
      .filter((el) => isEdge(el) && el.target === params.target)
      .map((el) => el.source);

    updateParents(params.target, parents);
    setElements((els) => addEdge({ ...params, arrowHeadType: "arrow" }, els));
  };

  const onElementsRemove = (elementsToRemove) => {
    setElements((els) => removeElements(elementsToRemove, els));
    elementsToRemove.forEach((el) => {
      if (isNode(el)) {
        client.action(window.schema, ["workflows", "api", "nodes", "delete"], {
          id: el.id,
        });
      } else {
        const parents = elements
          .filter(
            (currEl) =>
              isEdge(currEl) &&
              currEl.target === el.target &&
              currEl.source !== el.source
          )
          .map((currEl) => currEl.source);

        updateParents(el.target, parents);
      }
    });
  };

  const onEdgeUpdate = (oldEdge, newEdge) => {
    // User changed the target
    if (oldEdge.source === newEdge.source) {
      // We need to remove the source from the previous target and
      // add it to the new one
      const oldParents = elements
        .filter(
          (el) =>
            isEdge(el) &&
            el.target === oldEdge.target &&
            el.source !== oldEdge.source
        )
        .map((el) => el.source);
      updateParents(oldEdge.target, oldParents);

      const newParents = elements
        .filter((el) => isEdge(el) && el.target === newEdge.target)
        .map((el) => el.source);
      updateParents(newEdge.target, [...newParents, newEdge.source]);
    }
    // User changed the source
    else {
      // We only need to replace to old source with the new
      const parents = elements
        .filter(
          (el) =>
            isEdge(el) &&
            el.target === oldEdge.target &&
            el.source !== oldEdge.source
        )
        .map((el) => el.source);
      updateParents(newEdge.target, [...parents, newEdge.source]);
    }
    setElements((els) => updateEdge(oldEdge, newEdge, els));
  };

  const removeById = (id: string) => {
    const elemenToRemove = elements.filter((el) => el.id === id);
    onElementsRemove(elemenToRemove);
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
          <ActionContext.Provider value={{ removeById }}>
            <ReactFlow
              nodeTypes={defaultNodeTypes}
              elements={elements}
              onConnect={onConnect}
              onElementsRemove={onElementsRemove}
              onEdgeUpdate={onEdgeUpdate}
              onLoad={onLoad}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onNodeDragStop={onDragStop}
            >
              <Controls />
            </ReactFlow>
          </ActionContext.Provider>
        </div>
        <Sidebar />
      </ReactFlowProvider>
    </div>
  );
};

const DeleteButton = ({ id }) => {
  const { removeById } = useContext(ActionContext);
  return (
    <button onClick={() => removeById(id)}>
      <i className="fal fa-times fa-lg"></i>
    </button>
  );
};

const OpenButton = ({ id }) => {
  const workflowId = window.location.pathname.split("/")[4];

  return (
    <button
      data-src={`/workflows/${workflowId}/nodes/${id}`}
      data-action="click->tf-modal#open"
    >
      Settings
    </button>
  );
};

const Buttons = ({ id }) => {
  return (
    <div className="absolute -bottom-6 flex gap-4">
      <OpenButton id={id} />
      <DeleteButton id={id} />
    </div>
  );
};

const InputNode = ({ id, data, isConnectable, selected }: NodeProps) => (
  <>
    {selected && <Buttons id={id} />}
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
    {selected && <Buttons id={id} />}
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
}: NodeProps) => {
  return (
    <>
      {selected && <Buttons id={id} />}
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
};

const defaultNodeTypes = {
  input: InputNode,
  output: OutputNode,
  default: DefaultNode,
};

const ActionContext = createContext({ removeById: (id: string) => {} });

export default DnDFlow;
