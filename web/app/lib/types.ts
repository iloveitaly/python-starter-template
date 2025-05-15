// type Id<T> = T extends object ? {} & { [P in keyof T]: Id<T[P]> } : T
// expands object types one level deep
// eslint-disable-next-line @typescript-eslint/no-unused-vars
type Expand<T> = T extends infer O ? { [K in keyof O]: O[K] } : never
// eslint-disable-next-line @typescript-eslint/no-unused-vars
type ExpandRecursively<T> = T extends object
  ? T extends infer O
    ? { [K in keyof O]: ExpandRecursively<O[K]> }
    : never
  : T
