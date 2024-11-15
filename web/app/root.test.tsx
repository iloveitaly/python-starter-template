import { RouterProvider, createMemoryRouter } from "react-router"
import { describe, expect, it } from "vitest"

import App from "./root"
import { render, screen } from "@testing-library/react"

describe("Root App", () => {
  it("renders without crashing", () => {
    const router = createMemoryRouter([
      {
        path: "/",
        element: <App />,
        children: [
          {
            path: "/",
            element: <div>Test content</div>,
          },
        ],
      },
    ])

    render(<RouterProvider router={router} />)
    expect(screen.getByText("Test content")).toBeInTheDocument()
  })
})
