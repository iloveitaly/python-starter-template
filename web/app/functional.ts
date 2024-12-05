/*
JS functional tooling is terrible by default, this should be the single entrypoint for all additional functional tooling
*/
import * as R from "ramda"

// TODO is there a ramda thing for this
export function toNum(num: string | number) {
  if (typeof num === "string") {
    return parseInt(num, 10)
  } else {
    return num
  }
}

// TODO should add to ramda library
// would be better if we could construct this using lambda> R.and(R.isNil, R.compose(R.isEmpty, R.trim))(null)
export function isBlank(v: string | null | undefined) {
  if (R.isNil(v)) {
    return true
  }

  return R.compose(R.isEmpty, R.trim)(v)
}

// TODO the default isEmpty returns false on nil/undefined!
export const isEmpty = R.either(R.isNil, R.isEmpty)

export function arrayWrap(v: never) {
  if (Array.isArray(v)) {
    return v
  }

  return [v]
}

export default { isNil: R.isNil, isEmpty, isBlank, arrayWrap }
