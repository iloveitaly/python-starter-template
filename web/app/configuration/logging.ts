/**
 * Originally, we were using loglevel. tslog is typescript-by-default, has JSON support, and is a bit more modern.
 */
import { type ILogObj, LogLevel, Logger, type TLogLevelName } from "tslog"

import { isProduction } from "~/utils/environment"

let loggerInstance: Logger<ILogObj> | undefined

function prettySettings() {
  const prettyPrefix = "[{{hh}}:{{MM}}:{{ss}}] {{logLevelName}}"
  const pretty = {
    template: isProduction()
      ? `${prettyPrefix}: `
      : `${prettyPrefix} [{{filePathWithLine}}]: `,
    // https://github.com/fullstack-build/tslog/blob/v5.2.0/README.md#interactive-objects-in-the-browser-console-prettypassobjectsnatively
    levelMethod: {
      WARN: console.warn,
      ERROR: console.error,
      FATAL: console.error,
    },
  }

  if (isProduction()) return pretty

  return {
    ...pretty,
    errorStackTemplate:
      "  • {{fileNameWithLine}}\t{{method}}\n\t{{filePathWithLine}}",
  }
}

function configureLogging() {
  if (loggerInstance) return loggerInstance

  const defaultMinLevel = isProduction() ? LogLevel.WARN : LogLevel.INFO

  loggerInstance = new Logger({
    minLevel: defaultMinLevel,
    type: "pretty",
    pretty: prettySettings(),
    // whether each log walks the call stack to attach file/line
    stack: {
      capture: isProduction() ? "off" : "auto",
    },
    mask: {
      keys: ["password", "token", "secret", "authorization", "apiKey"],
      caseInsensitive: true,
    },
    strictConfig: !isProduction(),
  })

  // determine the log level from the environment variable
  if (import.meta.env.VITE_LOG_LEVEL) {
    loggerInstance.setMinLevel(
      import.meta.env.VITE_LOG_LEVEL.toUpperCase() as TLogLevelName,
    )
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
