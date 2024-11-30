// adapted from: https://johnsmilga.com/articles/2024/10/15
import { afterEach, expect } from "vitest"

import * as matchers from "@testing-library/jest-dom/matchers"
import "@testing-library/jest-dom/vitest"
import { cleanup } from "@testing-library/react"

expect.extend(matchers)

afterEach(() => {
  cleanup()
})
