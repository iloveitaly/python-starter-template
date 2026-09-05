/**
 * Originally, we were using loglevel. tslog is typescript-by-default, has JSON support, and is a bit more modern.
 */
import { type ILogObj, LogLevel, Logger } from "tslog"

import { isProduction } from "~/utils/environment"

let loggerInstance: Logger<ILogObj> | undefined

function configureLogging() {
  if (loggerInstance) return loggerInstance

  const defaultMinLevel = isProduction() ? LogLevel.WARN : LogLevel.INFO

  loggerInstance = new Logger({
    minLevel: defaultMinLevel,
    type: "pretty",
    pretty: {
      template: "[{{hh}}:{{MM}}:{{ss}}] {{logLevelName}}: ",
    },
    stack: {
      capture: isProduction() ? "off" : "auto",
    },
  })

  // determine the log level from the environment variable
  if (import.meta.env.VITE_LOG_LEVEL) {
    loggerInstance.setMinLevel(import.meta.env.VITE_LOG_LEVEL)
  }

  // this *could* occur intentionally, but it should be rare and it's ok to be noisy when it happens
  if (isDebugEnabled() && isProduction()) {
    loggerInstance.error("debug logging is enabled in production")
  }

  return loggerInstance
}

const log = configureLogging()

// intended to be used to enable verbose logging on various libraries that have a `debug` flag
export function isDebugEnabled(): boolean {
  const logger = loggerInstance || configureLogging()
  return logger.isLevelEnabled(LogLevel.DEBUG)
}

export { log }
export default { log }
