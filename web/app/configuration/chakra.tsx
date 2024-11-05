import { ChakraProvider, defaultSystem } from "@chakra-ui/react"

export default function withChakraProvider(Component: React.ComponentType) {
  return (props: any) => (
    <ChakraProvider value={defaultSystem}>
      <Component {...props} />
    </ChakraProvider>
  )
}
