// The "User action needed" pane for the backend-investigation skill. The skill writes its asks to
// USER-ACTIONS.md in the investigation directory; this module shows them and tells the model when
// the developer presses Done. It does nothing at all until a Write or Edit lands on that file name,
// so sessions that never use the skill read nothing, write nothing and draw nothing.
import { atom, read, update } from 'claude-code'
import type { Engine, Register } from 'claude-code'

import type { UserAction } from './types'

export const FILE_NAME = 'USER-ACTIONS.md'
const PANE = 'user-actions'
const items = atom({ plugin: 'newtab', key: 'userActions' } as const, [])
const file = atom({ plugin: 'newtab', key: 'userActionsFile' } as const, '')

// `- [ ] text` is open, `- [x] text` is done; every other line is ignored.
export const parse = (text: string): UserAction[] =>
  text.split('\n').flatMap(line => {
    const m = line.match(/^\s*- \[( |x)\] (.+)$/i)
    return m ? [{ isDone: m[1] !== ' ', text: m[2].trim() }] : []
  })

const isUserActionsFile = (path: string) => path.split('/').pop() === FILE_NAME

const isPanePlaced = async ($: Engine) =>
  (await $.ui.panes()).some(pane => pane.id === PANE && pane.isPlaced)

const sync = async ($: Engine, path: string) => {
  const list = parse((await $.fs.read(path)) as string)
  await update($, file, () => path)
  await update($, items, () => list)
  if (list.some(item => !item.isDone)) {
    await $.ui.open({ id: PANE, title: 'User action needed' })
  } else {
    await $.ui.close({ id: PANE })
  }
  return list
}

const markDone = async ($: Engine, item: UserAction) => {
  const path = await read($, file)
  const text = (await $.fs.read(path)) as string
  await $.fs.write(path, text.replace(`- [ ] ${item.text}`, `- [x] ${item.text}`))
  const list = await sync($, path)
  await $.session.append({
    message: {
      type: 'user',
      content: [{ type: 'text', text: `The developer pressed Done on this user action in the User action needed pane: ${item.text}. Verify it before relying on it.` }],
    },
  })
  return list
}

async function renderList($: Engine, e: Parameters<Engine['ui']['resolve']>[0]) {
  const { Box, Text, Button } = $.ui.resolve(e)
  const list = await read($, items)
  return (
    <Box flexDirection="column">
      {list.map((item, n) =>
        item.isDone ? (
          <Text dimColor>✓ {item.text}</Text>
        ) : (
          <Box flexDirection="row">
            <Button key={`done-${item.text}`} label="Done" hotkey={n < 9 ? String(n + 1) : undefined} onPress={() => void markDone($, item)} />
            <Text> {item.text}</Text>
          </Box>
        ),
      )}
    </Box>
  )
}

export const register: Register = on => {
  // Set by the first write to USER-ACTIONS.md; until then the band hook returns before touching $.
  let isActive = false

  for (const tool of ['Write', 'Edit'] as const) {
    on('tool.call', { tool }, async ($, e, next) => {
      const ran = await next(e)
      if (!isUserActionsFile(e.file_path) || ran.deny !== undefined || ran.isError) return ran
      isActive = true
      const list = await sync($, e.file_path)
      const open = list.filter(item => !item.isDone).length
      const where = (await isPanePlaced($)) ? 'the User action needed pane' : 'the band above the prompt'
      return { ...ran, context: [...(ran.context ?? []), `${open} open user action(s) are shown to the developer in ${where}. When they press Done you will be told.`] }
    }).catch(($, e, next) => next(e)) // never let the pane get in the way of the write itself
  }

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => renderList($, e))

  // A pane opened unasked waits undrawn in a narrow terminal; show the asks above the prompt instead.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (!isActive) return next(e)
    const list = await read($, items)
    const isOpen = (await $.ui.panes()).some(pane => pane.id === PANE)
    if (e.props.hasSurvey || !list.some(item => !item.isDone) || !isOpen || (await isPanePlaced($))) return next(e)
    return renderList($, e)
  })
}
