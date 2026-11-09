// Hosted read-only copy of one finished run, served on Vercel without the Python backend.
// Pages read saved responses from snapshot/; the two chats call the OpenAI-compatible
// model set in the Vercel env vars (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME).

const crypto = require('crypto')
const fs = require('fs')
const path = require('path')

// Public: this repo is public, so anyone who reads it can log in
const ADMIN_USERNAME = 'admin'
const ADMIN_PASSWORD = 'casella123'
const TOKEN = crypto.createHash('sha256').update(`rayfish:${ADMIN_USERNAME}:${ADMIN_PASSWORD}`).digest('hex')

const EMPTY_REPLY_ATTEMPTS = 3
const SNAPSHOT_DIR = path.join(process.cwd(), 'snapshot')
const cache = {}

function load(name) {
  if (!cache[name]) {
    cache[name] = JSON.parse(fs.readFileSync(path.join(SNAPSHOT_DIR, name), 'utf8'))
  }
  return cache[name]
}

function send(res, status, body) {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json; charset=utf-8')
  res.end(JSON.stringify(body))
}

async function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')
  } catch {
    return {}
  }
}

async function askModel(messages) {
  const model = process.env.LLM_MODEL_NAME || 'gpt-5-mini'
  const baseUrl = (process.env.LLM_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, '')
  // Reasoning models reject temperature and count reasoning against the token limit
  const isReasoningModel = /^(gpt-5|o\d)/.test(model)
  const payload = isReasoningModel
    ? { model, messages, max_completion_tokens: 4000 }
    : { model, messages, max_tokens: 4000, temperature: 0.7 }

  for (let attempt = 0; attempt < EMPTY_REPLY_ATTEMPTS; attempt++) {
    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.LLM_API_KEY}`,
      },
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      throw new Error(`The model request failed (HTTP ${response.status})`)
    }
    const data = await response.json()
    const text = (data.choices?.[0]?.message?.content || '')
      .replace(/<think>[\s\S]*?<\/think>/g, '')
      .trim()
    if (text) return text
  }
  throw new Error('The model returned no reply')
}

function personaMessages(persona, question) {
  const sections = Object.entries(persona.activity).map(([platform, lines]) => {
    const body = lines.length ? lines.join('\n') : '(no written posts or comments)'
    return `What you wrote on ${platform[0].toUpperCase()}${platform.slice(1)}:\n${body}`
  })
  const system =
    `You are ${persona.name || 'this persona'}, a simulated persona from a market simulation. ` +
    'You are not a real person. Stay in character.\n\n' +
    `Your profile:\n${persona.persona}\n\n` +
    sections.join('\n\n') +
    "\n\nBase your answer on this profile and what you wrote. Don't invent posts, purchases, " +
    "test results or experiences that aren't listed. If your saved activity doesn't cover the " +
    'question, say so, then give the view your profile suggests. ' +
    'Reply in the language of the question, in under 150 words.'
  return [
    { role: 'system', content: system },
    { role: 'user', content: question },
  ]
}

async function interview(body) {
  const personas = load('personas.json')
  const answers = await Promise.all((body.interviews || []).map(async ({ agent_id: agentId, prompt }) => {
    const persona = personas[agentId]
    if (!persona) throw new Error(`Unknown agent_id: ${agentId}`)
    const response = await askModel(personaMessages(persona, prompt))
    return { agent_id: agentId, response, platform: 'saved', reconstructed: true }
  }))
  const results = Object.fromEntries(answers.map(a => [`saved_${a.agent_id}`, a]))
  return { success: true, reconstructed: true, result: { interviews_count: answers.length, results } }
}

async function reportChat(body) {
  const report = load('report.json')
  const system =
    'You are the Report Agent for a market simulation. Answer questions about the report below. ' +
    'The people in it are simulated AI personas, not real users, so never present their views as ' +
    "customer evidence. If the report doesn't cover a question, say so instead of guessing. " +
    'Reply in the language of the question.\n\n' +
    `Simulation brief:\n${report.simulation_requirement}\n\nReport:\n${report.markdown}`
  const history = (body.chat_history || [])
    .filter(m => (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
    .slice(-10)
  const messages = [{ role: 'system', content: system }, ...history, { role: 'user', content: String(body.message || '') }]
  return { response: await askModel(messages), tool_calls: [], sources: [] }
}

// Saved responses were recorded from the first page load. Later log polls ask for
// lines after the end, so they get an empty page.
function savedResponse(pathname, query) {
  if (pathname === '/api/graph/data/mirofish_ee5e9678cc134449') return load('graph.json')
  const responses = load('responses.json')
  const fromLine = Number(query.get('from_line') || 0)
  if (/\/(agent|console)-log$/.test(pathname) && fromLine > 0) {
    const first = responses[`${pathname}?from_line=0`]
    if (!first) return null
    return { success: true, data: { logs: [], from_line: fromLine, has_more: false, total_lines: first.data.total_lines } }
  }
  return responses[`${pathname}${query.toString() ? `?${query}` : ''}`] || responses[pathname] || null
}

module.exports = async function handler(req, res) {
  const url = new URL(req.url, 'http://localhost')
  const rewritten = url.searchParams.get('path')
  url.searchParams.delete('path')
  const pathname = rewritten ? `/api/${rewritten}` : url.pathname

  try {
    if (req.method === 'POST' && pathname === '/api/auth/login') {
      const body = await readBody(req)
      if (body.username === ADMIN_USERNAME && body.password === ADMIN_PASSWORD) {
        return send(res, 200, { success: true, data: { token: TOKEN } })
      }
      return send(res, 401, { success: false, error: 'Invalid username or password' })
    }

    if (req.headers.authorization !== `Bearer ${TOKEN}`) {
      return send(res, 401, { success: false, error: 'Login required' })
    }

    if (req.method === 'GET') {
      const saved = savedResponse(pathname, url.searchParams)
      return saved
        ? send(res, 200, saved)
        : send(res, 404, { success: false, error: 'Not available in the hosted copy' })
    }

    if (req.method === 'POST' && pathname === '/api/simulation/env-status') {
      return send(res, 200, { success: true, data: { twitter_available: false, reddit_available: false } })
    }
    if (req.method === 'POST' && pathname === '/api/simulation/interview/batch') {
      return send(res, 200, { success: true, data: await interview(await readBody(req)) })
    }
    if (req.method === 'POST' && pathname === '/api/report/chat') {
      return send(res, 200, { success: true, data: await reportChat(await readBody(req)) })
    }

    return send(res, 400, { success: false, error: 'The hosted copy is read-only. Run it locally to do this.' })
  } catch (err) {
    return send(res, 500, { success: false, error: err.message })
  }
}
