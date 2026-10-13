import { expect, test } from 'claude-code/testing'

import { parse } from './register'

const DIR = '/tmp/inv/oct13-empty-de'
const answerWrite = { result: { type: 'create', filePath: '', content: '', structuredPatch: [], originalFile: null } }

test('parse reads open and done items and ignores everything else', () => {
  expect(parse('# Asks\n- [ ] run gcloud auth login\n- [x] connect VPN\nnotes')).toEqual([
    { isDone: false, text: 'run gcloud auth login' },
    { isDone: true, text: 'connect VPN' },
  ])
})

test('a write to any other file touches nothing', async ($, on) => {
  const touched: string[] = []
  on('tool.call', () => answerWrite as never)
  on('fs.read', () => { touched.push('fs.read'); return { value: '' } })
  on('ui.open', () => { touched.push('ui.open'); return { value: { isPlaced: true } } as never })

  await $.tool.call({ tool: 'Write', file_path: `${DIR}/FINDINGS.md`, content: '- [ ] not an ask' })

  expect(touched).toEqual([])
})

test('writing USER-ACTIONS.md opens the pane and tells the model', async ($, on) => {
  const opened: string[] = []
  on('tool.call', () => answerWrite as never)
  on('fs.read', () => ({ value: '- [ ] run gcloud auth login\n' }))
  on('ui.open', (_$, e) => { opened.push(e.id); return { value: { isPlaced: true } } as never })
  on('ui.panes', () => ({ value: [{ id: 'user-actions', isPlaced: true }] }) as never)

  const ran = await $.tool.call({ tool: 'Write', file_path: `${DIR}/USER-ACTIONS.md`, content: '' })

  expect(opened).toEqual(['user-actions'])
  expect(JSON.stringify(ran)).toContain('1 open user action(s) are shown to the developer in the User action needed pane')
})
