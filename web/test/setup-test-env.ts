// adapted from: https://johnsmilga.com/articles/2024/10/15
import nock from "nock"
import { afterEach, expect } from "vitest"

import * as matchers from "@testing-library/jest-dom/matchers"
import "@testing-library/jest-dom/vitest"
import { cleanup } from "@testing-library/react"

// happy-dom blocks external <script src="..."> execution by default, which prevents SDK bundles
// like PostHog/Clerk from loading in tests.
//
// nock is still useful as a second layer: it blocks accidental external HTTP calls (fetch/xhr/http)
// so tests remain deterministic even if runtime behavior changes.
nock.disableNetConnect()
nock.enableNetConnect((host: string) => {
  return host.startsWith("127.0.0.1") || host.startsWith("localhost")
})

// Keep this explicit PostHog stub for stability across environment/runtime differences.
nock(/posthog\.com/)
  .persist()
  .get(/.*/)
  .reply(200, "")

expect.extend(matchers)

afterEach(() => {
  cleanup()
})
