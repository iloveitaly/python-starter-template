// TODO why do I need ../? I couldn't get .react-router to play well
// import * as Route from "/.react-router/types/app/+types.root"
import { type MetaFunction } from "react-router"

import { AppSidebar } from "~/components/app-sidebar"
import {
    Breadcrumb,
    BreadcrumbItem,
    BreadcrumbLink,
    BreadcrumbList,
    BreadcrumbPage,
    BreadcrumbSeparator,
} from "~/components/ui/breadcrumb"
import { Separator } from "~/components/ui/separator"
import {
    SidebarInset,
    SidebarProvider,
    SidebarTrigger,
} from "~/components/ui/sidebar"
import { getClient } from "~/configuration/clerk"
import { applicationData } from "~/configuration/client"

import type { Route } from "./+types.home"
import { invariant } from "@epic-web/invariant"

export const meta: MetaFunction = () => {
    return [
        { title: "Starter Application Template" },
        {
            name: "description",
            content: "Welcome to Starter Application Template",
        },
    ]
}

export async function clientLoader(_loader_args: Route.ClientLoaderArgs) {
    const clerkClient = await getClient()
    invariant(clerkClient, "clerk client should always exist or redirect")

    // this route is authenticated
    const { data } = await applicationData()

    // TODO need idiomatic error handling here
    if (data === undefined) {
        throw new Error("Failed to load data")
    }

    return data
}

export default function Page({ loaderData }: Route.ComponentProps) {
    return (
        <SidebarProvider
            style={
                {
                    "--sidebar-width": "350px",
                } as React.CSSProperties
            }
        >
            <AppSidebar />
            <SidebarInset>
                <header className="sticky top-0 flex shrink-0 items-center gap-2 border-b bg-background p-4">
                    <SidebarTrigger className="-ml-1" />
                    <Separator orientation="vertical" className="mr-2 h-4" />
                    <Breadcrumb>
                        <BreadcrumbList>
                            <BreadcrumbItem className="hidden md:block">
                                <BreadcrumbLink href="#">
                                    All Inboxes
                                </BreadcrumbLink>
                            </BreadcrumbItem>
                            <BreadcrumbSeparator className="hidden md:block" />
                            <BreadcrumbItem>
                                <BreadcrumbPage>Inbox</BreadcrumbPage>
                            </BreadcrumbItem>
                        </BreadcrumbList>
                    </Breadcrumb>
                </header>
                <div className="flex flex-1 flex-col gap-4 p-4">
                    {loaderData && loaderData.message}
                    {Array.from({ length: 24 }).map((_, index) => (
                        <div
                            key={index}
                            className="aspect-video h-12 w-full rounded-lg bg-muted/50"
                        />
                    ))}
                </div>
            </SidebarInset>
        </SidebarProvider>
    )
}

// export default function Home({ loaderData }: Route.ComponentProps) {
//   return (
//     <div className="flex h-screen items-center justify-center">
//       <div className="flex flex-col items-center gap-16">
//         <header className="flex flex-col items-center gap-9">
//           <h1 className="leading text-2xl font-bold text-gray-800 dark:text-gray-100">
//             {loaderData && loaderData.message}
//             <span className="sr-only">React Router</span>
//           </h1>
//           <div className="w-[500px] max-w-[100vw] p-4">
//             <img
//               src="/logo-light.svg"
//               alt="React Router"
//               className="block w-full dark:hidden"
//             />
//             <img
//               src="/logo-dark.svg"
//               alt="React Router"
//               className="hidden w-full dark:block"
//             />
//           </div>
//         </header>
//       </div>
//     </div>
//   )
// }
