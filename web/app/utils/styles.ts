/**
 * Custom site-specific cva styles
 */
import { cva } from "class-variance-authority"

// ex: customButtonVariants({ variant: "primary" })
export const customButtonVariants = cva("w-full", {
  variants: {
    variant: {
      primary:
        "bg-cta-orange/90 font-bold hover:bg-cta-orange hover:cursor-pointer",
      green:
        "bg-green-600 px-4 py-2 text-base font-semibold text-white hover:cursor-pointer hover:bg-green-700",
    },
  },
})
