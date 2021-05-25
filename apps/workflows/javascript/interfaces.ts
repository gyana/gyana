export interface INode {
  [kind: string]: {
    displayName: string;
    icon: string;
    description: string;
    section: string;
    maxParents?: number;
  };
}
