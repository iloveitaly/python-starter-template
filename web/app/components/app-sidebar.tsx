import * as React from "react"

import { ArchiveX, Command, File, Inbox, Send, Trash2 } from "lucide-react"

import { NavUser } from "~/components/nav-user"
import { Label } from "~/components/ui/label"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarInput,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "~/components/ui/sidebar"
import { Switch } from "~/components/ui/switch"

import { UserButton } from "~/configuration/clerk"

// This is sample data
const data = {
  user: {
    name: "shadcn",
    email: "m@example.com",
    avatar: "/avatars/shadcn.jpg",
  },
  navMain: [
    {
      title: "Inbox",
      url: "#",
      icon: Inbox,
      isActive: true,
    },
    {
      title: "Drafts",
      url: "#",
      icon: File,
      isActive: false,
    },
    {
      title: "Sent",
      url: "#",
      icon: Send,
      isActive: false,
    },
    {
      title: "Junk",
      url: "#",
      icon: ArchiveX,
      isActive: false,
    },
    {
      title: "Trash",
      url: "#",
      icon: Trash2,
      isActive: false,
    },
  ],
  mails: [
    {
      name: "William Smith",
      email: "williamsmith@example.com",
      subject: "Meeting Tomorrow",
      date: "09:34 AM",
      teaser:
        "Hi team, just a reminder about our meeting tomorrow at 10 AM.\nPlease come prepared with your project updates." +
        "Hi team, just a reminder about our meeting tomorrow at 10 AM.\nPlease come prepared with your project updates.",
    },
    // ... other mails
  ],
}

type NavItem = (typeof data.navMain)[number]
type Mail = (typeof data.mails)[number]

interface NavigationSidebarProps {
  activeItem: NavItem
  setActiveItem: React.Dispatch<React.SetStateAction<NavItem>>
  setMails: React.Dispatch<React.SetStateAction<Mail[]>>
}

export function NavigationSidebar({
  activeItem,
  setActiveItem,
  setMails,
}: NavigationSidebarProps) {
  const { setOpen } = useSidebar()

  return (
    <Sidebar
      collapsible="none"
      className="!w-[calc(var(--sidebar-width-icon)_+_1px)] border-r"
    >
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild className="md:h-8 md:p-0">
              <a href="#">
                <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <Command className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">Acme Inc</span>
                  <span className="truncate text-xs">Enterprise</span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent className="px-1.5 md:px-0">
            <SidebarMenu>
              {data.navMain.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    tooltip={{ children: item.title, hidden: false }}
                    onClick={() => {
                      setActiveItem(item)
                      const randomizedMails = data.mails.sort(
                        () => Math.random() - 0.5,
                      )
                      setMails(
                        randomizedMails.slice(
                          0,
                          Math.max(5, Math.floor(Math.random() * 10) + 1),
                        ),
                      )
                      setOpen(true)
                    }}
                    isActive={activeItem.title === item.title}
                    className="px-2.5 md:px-2"
                  >
                    <item.icon />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <UserButton />
      </SidebarFooter>
    </Sidebar>
  )
}

interface MailSidebarProps {
  activeItem: NavItem
  mails: Mail[]
}

export function MailSidebar({ activeItem, mails }: MailSidebarProps) {
  return (
    <Sidebar collapsible="none" className="hidden flex-1 border-r md:flex">
      <SidebarHeader className="gap-3.5 border-b p-4">
        <div className="flex w-full items-center justify-between">
          <div className="text-foreground text-base font-medium">
            {activeItem.title}
          </div>
          <Label className="flex items-center gap-2 text-sm">
            <span>Unreads</span>
            <Switch className="shadow-none" />
          </Label>
        </div>
        <SidebarInput placeholder="Type to search..." />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup className="px-0">
          <SidebarGroupContent>
            {mails.map((mail) => (
              <a
                href="#"
                key={mail.email}
                className="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 border-b p-4 text-sm leading-tight whitespace-nowrap last:border-b-0"
              >
                <div className="flex w-full items-center gap-2">
                  <span>{mail.name}</span>
                  <span className="ml-auto text-xs">{mail.date}</span>
                </div>
                <span className="font-medium">{mail.subject}</span>
                <span className="line-clamp-2 w-[260px] text-xs whitespace-break-spaces">
                  {mail.teaser}
                </span>
              </a>
            ))}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const [activeItem, setActiveItem] = React.useState<NavItem>(data.navMain[0])
  const [mails, setMails] = React.useState<Mail[]>(data.mails)

  return (
    <div
      collapsible="icon"
      // className="overflow-hidden [&>[data-sidebar=sidebar]]:flex-row"
      className="flex"
      {...props}
    >
      <NavigationSidebar
        activeItem={activeItem}
        setActiveItem={setActiveItem}
        setMails={setMails}
      />
      <MailSidebar activeItem={activeItem} mails={mails} />
    </div>
  )
}
