import React from "react"

// These are "Mock" components. They just return their children
// without checking for any security keys.
export const SignedIn = ({ children }: { children: React.ReactNode }) => <>{children}</>
export const SignedOut = ({ children }: { children: React.ReactNode }) => null
export const UserButton = () => <div style={{background: '#333', color: 'white', padding: '5px'}}>User</div>
export const ClerkProvider = ({ children }: { children: React.ReactNode }) => <>{children}</>

// A dummy key for the config
export const CLERK_PUBLIC_KEY = "pk_test_placeholder"

// Fake client for the generator
export async function getClient() {
  return {
    loaded: true,
    user: { id: "user_keith", firstName: "Keith" },
    getToken: async () => "dummy-token"
  }
}

// The Provider wrapper used in index.ts
export default function withClerkProvider(Component: React.ComponentType) {
  return (props: any) => (
    <Component {...props} />
  )
}
