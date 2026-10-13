export type UserAction = { text: string; isDone: boolean }

declare module 'claude-code' {
  interface PluginState {
    newtab: { userActions: UserAction[]; userActionsFile: string }
  }
}
