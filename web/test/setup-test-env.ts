// adapted from: https://johnsmilga.com/articles/2024/10/15
import nock from "nock"
import { afterEach, expect } from "vitest"

import * as matchers from "@testing-library/jest-dom/matchers"
import "@testing-library/jest-dom/vitest"
import { cleanup } from "@testing-library/react"

// without nock, posthog and other services will attempt to load and cause tests to be flakey
nock.disableNetConnect()
nock.enableNetConnect((host: string) => {
  return host.startsWith("127.0.0.1") || host.startsWith("localhost")
})

nock(/posthog\.com/)
  .persist()
  .get(/.*/)
  .reply(200, "")

expect.extend(matchers)

afterEach(() => {
  cleanup()
})
