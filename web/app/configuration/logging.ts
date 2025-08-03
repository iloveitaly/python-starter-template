/**
 * Originally, we were using loglevel. tslog is typescript-by-default, has JSON support, and is a bit more modern.
 */
import { ILogObj, Logger } from "tslog"

// ILogLevel
import { isProduction } from "~/utils/environment"

let loggerInstance: Logger<ILogObj> | undefined

// TODO https://github.com/fullstack-build/tslog/pull/308
// it's insane, but this mapping does not exist in tslog :/
// I've removed the levels that are... silly
const LOG_LEVEL_MAP: Record<string, number> = {
  // silly: 0,
  trace: 1,
  debug: 2,
  info: 3,
  warn: 4,
  error: 5,
  fatal: 6,
  // silent: 7,
}

function configureLogging() {
  if (loggerInstance) return loggerInstance

  const DEFAULT_LOG_LEVEL: number = isProduction()
    ? LOG_LEVEL_MAP.warn
    : LOG_LEVEL_MAP.info

  loggerInstance = new Logger({
    minLevel: DEFAULT_LOG_LEVEL,
    type: "pretty",
    prettyLogTemplate: "[{{hh}}:{{MM}}:{{ss}}] {{logLevelName}}: ",
    hideLogPositionForProduction: isProduction(),
  })

  // determine the log level from the environment variable
  if (import.meta.env.VITE_LOG_LEVEL) {
    const logLevelFromEnv = import.meta.env.VITE_LOG_LEVEL.toLowerCase()
    loggerInstance.settings.minLevel =
      LOG_LEVEL_MAP[logLevelFromEnv] ?? DEFAULT_LOG_LEVEL
  }

  return loggerInstance
}

const log = configureLogging()

export { log }
export default { log }
