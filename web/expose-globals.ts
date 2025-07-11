import fs from "fs"
import { Plugin, ResolvedConfig } from "vite"

import path from "path"

export interface ExposeConfig {
  /** Path to the module to import (relative to project root or aliased) */
  from: string
  /** Global name for the exposed module (required if no members specified) */
  globalName?: string
  /**
   * Specific members to expose
   * - Array: expose with original names
   * - Object: expose with custom names (key: global name, value: original name)
   */
  members?: string[] | Record<string, string>
}

export interface PluginOptions {
  /** Modules to expose */
  exposes: ExposeConfig | ExposeConfig[]
  /** Global object to attach to (default: 'window') */
  globalObject?: string
  /** Restrict exposures to development mode only (default: true) */
  devOnly?: boolean
}

export default function vitePluginExposeGlobals(
  options: PluginOptions,
): Plugin {
  const { globalObject = "window", devOnly = true } = options
  const exposes = Array.isArray(options.exposes)
    ? options.exposes
    : [options.exposes]

  const virtualModuleId = "virtual:expose-globals"
  const resolvedVirtualModuleId = "\0" + virtualModuleId
  let entryPath: string | undefined

  return {
    name: "vite:expose-globals",
    enforce: "post",
    configResolved(resolvedConfig) {
      // Fallback: Check common entry paths if no match in HTML, prioritizing root.tsx variants
      if (!entryPath) {
        const possibleEntries = [
          "app/root.tsx",
          "root.tsx",
          "src/main.ts",
          "src/main.js",
          "main.ts",
          "main.js",
        ]
        for (const rel of possibleEntries) {
          const full = path.resolve(resolvedConfig.root, rel)
          if (fs.existsSync(full)) {
            entryPath = full
            break
          }
        }
      }
    },
    resolveId(id) {
      if (id === virtualModuleId) {
        return resolvedVirtualModuleId
      }
      return null
    },
    load(id) {
      if (id === resolvedVirtualModuleId) {
        let code = `if (${devOnly ? "import.meta.env.DEV && " : ""}typeof ${globalObject} !== 'undefined') {\n`

        exposes.forEach((exp) => {
          if (!exp.from) return

          code += `import('${exp.from}').then(mod => {\n`

          if (exp.members) {
            if (Array.isArray(exp.members)) {
              exp.members.forEach((member) => {
                code += `${globalObject}.${member} = mod.${member};\n`
              })
            } else {
              Object.entries(exp.members).forEach(([exposed, original]) => {
                code += `${globalObject}.${exposed} = mod.${original};\n`
              })
            }
          } else if (exp.globalName) {
            code += `${globalObject}.${exp.globalName} = mod.default || mod;\n`
          }

          code += `}).catch(err => console.error('Failed to expose ${exp.from}:', err));\n`
        })

        code += "}"
        console.log("Exposing globals with code:\n", code)
        return code
      }
      return null
    },
    transform(code, id) {
      if (entryPath && path.resolve(id) === entryPath) {
        // Normalize for cross-platform comparison
        // Prepend the import to the entry file
        return `import '${virtualModuleId}';\n${code}`
      }
      return null
    },
  }
}
