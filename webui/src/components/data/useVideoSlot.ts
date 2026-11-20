import { useEffect, useRef, useState } from 'react'

const MAX_SLOTS = 6
let used = 0
const listeners = new Set<() => void>()

function emit() {
  listeners.forEach((listener) => listener())
}

/** 列表里同时只让少量视频挂上，用来取一帧画面。 */
export function useVideoSlot(visible: boolean): boolean {
  const held = useRef(false)
  const [granted, setGranted] = useState(false)

  useEffect(() => {
    const sync = () => {
      if (!visible) {
        setGranted(false)
        return
      }
      if (held.current) {
        setGranted(true)
        return
      }
      if (used >= MAX_SLOTS) {
        setGranted(false)
        return
      }
      used += 1
      held.current = true
      setGranted(true)
    }

    listeners.add(sync)
    sync()
    return () => {
      listeners.delete(sync)
      if (held.current) {
        held.current = false
        used -= 1
        emit()
      }
    }
  }, [visible])

  return granted
}
