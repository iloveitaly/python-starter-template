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

function mockGetRequests(hostPattern: RegExp | string) {
  nock(hostPattern as string)
    .persist()
    .get(/.*/)
    .reply(200, "")
}

for (const hostPattern of [/facebook\.(net|com)/]) {
  mockGetRequests(hostPattern)
}

expect.extend(matchers)

afterEach(() => {
  cleanup()
})
