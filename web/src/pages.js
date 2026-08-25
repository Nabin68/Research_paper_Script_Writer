/**
 * The Instagram pages this console drives. Research Paper is live; the rest are
 * on hold and will follow the same 5-stage shape once their pipelines exist.
 *
 * To bring a page online later: set status:'live' and point `agentSource` at
 * whatever the server exposes for it.
 */

export const PAGES = [
  {
    id: 'research-paper',
    name: 'Research Paper',
    handle: '@aiprofessor.vs',
    icon: 'paper',
    status: 'live',
    // children come from the server's agent catalog
    agentSource: true,
  },
  {
    id: 'open-source',
    name: 'Open Source',
    handle: 'planned',
    icon: 'code',
    status: 'hold',
  },
  {
    id: 'future-tech',
    name: 'Future Tech',
    handle: 'planned',
    icon: 'rocket',
    status: 'hold',
  },
  {
    id: 'decoding',
    name: 'Decoding',
    handle: 'planned',
    icon: 'decode',
    status: 'hold',
  },
]

/** The stage shape every page is expected to follow, shown greyed on held pages. */
export const PLANNED_STAGES = ['Finder', 'Picker', 'Deep-Dive', 'Writer', 'Refiner']

/** Icon per agent number, so the sidebar rows read at a glance. */
export const AGENT_ICONS = ['search', 'target', 'scope', 'pen', 'wand', 'caption']
