declare global {
  interface Window {
    schema: any
  }
}

export interface INode {
  [kind: string]: {
    displayName: string
    icon: string
    description: string
    section: string
    maxParents: number
  }
}

export const NODES = JSON.parse(
  (document.getElementById('nodes') as HTMLScriptElement).textContent as string
) as INode
