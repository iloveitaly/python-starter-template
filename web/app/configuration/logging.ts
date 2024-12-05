import type { LogLevelNames } from "loglevel"
import logger from "loglevel"
import logLevelPrefix from "loglevel-plugin-prefix"

let isLoggingConfigured = false

function configureLogging() {
    if (isLoggingConfigured) return logger
    isLoggingConfigured = true

    // TODO extract out to separate logging config
    // add expected log level prefixes
    logLevelPrefix.reg(logger)
    logger.enableAll()
    logLevelPrefix.apply(logger)

    if (import.meta.env.VITE_LOG_LEVEL) {
        const logLevelFromEnv =
            import.meta.env.VITE_LOG_LEVEL.toLowerCase() as LogLevelNames
        logger.setLevel(logLevelFromEnv)
    } else {
        logger.setLevel(logger.levels.INFO)
    }

    return logger
}

configureLogging()

export const log = logger
export default { log: logger }
