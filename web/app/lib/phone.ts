import { z } from "zod"

import { parsePhoneNumberFromString } from "libphonenumber-js"

function isPossiblePhoneNumber(value: string) {
  const phoneNumber = parsePhoneNumberFromString(value, "US")
  return phoneNumber?.isPossible() || false
}

function normalizeUsPhoneNumber(value: string) {
  const phoneNumber = parsePhoneNumberFromString(value, "US")

  if (phoneNumber?.country === "US" && phoneNumber.isPossible()) {
    return phoneNumber.number
  }

  return value
}

export function requiredPhoneSchema(requiredMessage = "Phone is required") {
  return z
    .string()
    .min(1, requiredMessage)
    .refine(isPossiblePhoneNumber, { message: "Invalid phone number" })
    .transform(normalizeUsPhoneNumber)
}

export function optionalPhoneSchema() {
  return z
    .string()
    .optional()
    .or(z.literal(""))
    .refine(
      (value) => {
        if (!value) {
          return true
        }

        return isPossiblePhoneNumber(value)
      },
      { message: "Invalid phone number" },
    )
}
