import { type ChildProcess, execFile, spawn } from 'node:child_process'
import http from 'node:http'
import type { IncomingMessage, ServerResponse } from 'node:http'
import type { Plugin } from 'vite'

type BackendError = 'uv_not_found' | 'start_timeout' | 'start_failed' | 'stop_failed'

type BackendStatus = {
  running: boolean
  starting: boolean
  stopping: boolean
  managed: boolean
  error: BackendError | null
  detail: string | null
}

const API_MARK = 'api.main:app'
const HEALTH_URL = 'http://127.0.0.1:8080/api/health'

let child: ChildProcess | null = null
let logTail = ''
let starting = false
let stopping = false
let lastError: BackendError | null = null
let lastDetail: string | null = null
let queue: Promise<void> = Promise.resolve()

function enqueue(task: () => Promise<void>) {
  const run = queue.then(task, task)
  queue = run.then(
    () => undefined,
    () => undefined,
  )
  return run
}

function remember(text: string) {
  logTail = (logTail + text).slice(-4000)
}

function healthcheck(): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(HEALTH_URL, { timeout: 1500 }, (res) => {
      res.resume()
      resolve(res.statusCode === 200)
    })
    req.on('error', () => resolve(false))
    req.on('timeout', () => {
      req.destroy()
      resolve(false)
    })
  })
}

function execText(command: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(command, args, { windowsHide: true, timeout: 15000 }, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(String(stderr || error.message)))
        return
      }
      resolve(String(stdout))
    })
  })
}

async function apiRootPids(): Promise<number[]> {
  try {
    return await listApiRootPids()
  } catch {
    return []
  }
}

async function listApiRootPids(): Promise<number[]> {
  if (process.platform === 'win32') {
    const script = [
      "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*api.main:app*' }",
      '$ids = @($procs | ForEach-Object { $_.ProcessId })',
      '$procs | Where-Object { $ids -notcontains $_.ParentProcessId } | ForEach-Object { $_.ProcessId }',
    ].join('; ')
    const output = await execText('powershell.exe', ['-NoProfile', '-Command', script])
    return output
      .split(/\s+/)
      .map((item) => Number(item))
      .filter((pid) => Number.isInteger(pid) && pid > 0)
  }

  const output = await execText('ps', ['-ax', '-o', 'pid=,ppid=,command='])
  const rows = output
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.includes(API_MARK))
    .map((line) => {
      const match = line.match(/^(\d+)\s+(\d+)\s+/)
      return match ? { pid: Number(match[1]), ppid: Number(match[2]) } : null
    })
    .filter((row): row is { pid: number; ppid: number } => row !== null)
  const ids = new Set(rows.map((row) => row.pid))
  return rows.filter((row) => !ids.has(row.ppid)).map((row) => row.pid)
}

async function killPid(pid: number) {
  if (process.platform === 'win32') {
    await execText('taskkill', ['/PID', String(pid), '/T', '/F'])
    return
  }
  try {
    process.kill(-pid, 'SIGTERM')
  } catch {
    process.kill(pid, 'SIGTERM')
  }
}

async function stopApiProcesses() {
  const pids = new Set<number>()
  if (child?.pid) pids.add(child.pid)
  for (const pid of await apiRootPids()) pids.add(pid)
  child = null
  for (const pid of pids) {
    try {
      await killPid(pid)
    } catch {
      // 进程可能已经退出，继续停其余进程
    }
  }
}

function waitFor(predicate: () => Promise<boolean>, timeoutMs: number) {
  const started = Date.now()
  return new Promise<boolean>((resolve) => {
    const tick = async () => {
      if (await predicate()) {
        resolve(true)
        return
      }
      if (Date.now() - started >= timeoutMs) {
        resolve(false)
        return
      }
      setTimeout(tick, 400)
    }
    void tick()
  })
}

async function readStatus(): Promise<BackendStatus> {
  return {
    running: await healthcheck(),
    starting,
    stopping,
    managed: child !== null && child.exitCode === null,
    error: lastError,
    detail: lastDetail,
  }
}

function sendJson(res: ServerResponse, status: number, body: unknown) {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json')
  res.end(JSON.stringify(body))
}

async function startBackend(projectRoot: string) {
  if (await healthcheck()) return
  if (child && child.exitCode === null) {
    const ready = await waitFor(healthcheck, 30000)
    if (!ready) {
      lastError = 'start_timeout'
      lastDetail = logTail.trim() || null
      throw new Error('start_timeout')
    }
    return
  }

  logTail = ''
  lastError = null
  lastDetail = null
  const spawned = spawn('uv', ['run', 'uvicorn', 'api.main:app', '--port', '8080', '--reload'], {
    cwd: projectRoot,
    windowsHide: true,
    detached: process.platform !== 'win32',
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  })
  child = spawned
  spawned.stdout?.on('data', (chunk: Buffer) => {
    const text = chunk.toString()
    remember(text)
    process.stdout.write(text)
  })
  spawned.stderr?.on('data', (chunk: Buffer) => {
    const text = chunk.toString()
    remember(text)
    process.stderr.write(text)
  })
  spawned.on('exit', () => {
    if (child === spawned) child = null
  })
  spawned.on('error', (error: NodeJS.ErrnoException) => {
    if (child === spawned) child = null
    lastError = error.code === 'ENOENT' ? 'uv_not_found' : 'start_failed'
    lastDetail = error.message
  })

  const ready = await new Promise<boolean>((resolve) => {
    const startedAt = Date.now()
    const tick = async () => {
      if (lastError === 'uv_not_found' || spawned.exitCode !== null) {
        resolve(false)
        return
      }
      if (await healthcheck()) {
        resolve(true)
        return
      }
      if (Date.now() - startedAt >= 30000) {
        resolve(false)
        return
      }
      setTimeout(tick, 400)
    }
    void tick()
  })

  if (ready) {
    lastError = null
    lastDetail = null
    return
  }
  if (lastError === 'uv_not_found') throw new Error('uv_not_found')
  lastError = spawned.exitCode !== null ? 'start_failed' : 'start_timeout'
  lastDetail = logTail.trim() || null
  throw new Error(lastError)
}

async function stopBackend() {
  await stopApiProcesses()
  const stopped = await waitFor(async () => !(await healthcheck()), 8000)
  if (!stopped) {
    lastError = 'stop_failed'
    lastDetail = null
    throw new Error('stop_failed')
  }
  lastError = null
  lastDetail = null
}

function handle(req: IncomingMessage, res: ServerResponse, projectRoot: string) {
  const path = (req.url || '').split('?')[0]
  if (path !== '/dev/backend' && path !== '/dev/backend/start' && path !== '/dev/backend/stop') return false

  if (req.method === 'GET' && path === '/dev/backend') {
    void readStatus().then((status) => sendJson(res, 200, status))
    return true
  }

  if (req.method === 'POST' && (path === '/dev/backend/start' || path === '/dev/backend/stop')) {
    const start = path.endsWith('/start')
    void enqueue(async () => {
      if (start) {
        starting = true
        try {
          await startBackend(projectRoot)
        } finally {
          starting = false
        }
        return
      }
      stopping = true
      try {
        await stopBackend()
      } finally {
        stopping = false
      }
    })
      .then(async () => sendJson(res, 200, await readStatus()))
      .catch(async (error: Error) => {
        const status = await readStatus()
        if (!status.error) status.error = (error.message as BackendError) || 'start_failed'
        sendJson(res, 500, status)
      })
    return true
  }

  sendJson(res, 405, { error: 'method_not_allowed' })
  return true
}

export function backendDevPlugin(projectRoot: string): Plugin {
  return {
    name: 'mediacrawler-backend-switch',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!handle(req, res, projectRoot)) next()
      })
      server.httpServer?.on('close', () => {
        const pid = child?.pid
        if (pid) void killPid(pid).catch(() => undefined)
      })
    },
  }
}
