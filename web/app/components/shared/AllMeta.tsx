/**
 * AllMeta Component
 *
 * This module provides a reusable React component for generating meta tags, including Open Graph (OG),
 * Twitter Cards, and Facebook-specific tags. It supports global defaults via a context provider and
 * per-instance overrides through props.
 *
 * Inspired by the vite-plugin-open-graph package, which generates similar meta tags for Vite applications.
 * Reference:
 * - https://github.com/Lmmmmmm-bb/vite-plugin-open-graph
 * - https://zhead.dev
 *
 *
 * Features:
 * - Renders essential SEO tags like <title> and <meta name="description">.
 * - Automatically generates OG equivalents for title and description.
 * - Handles nested structures for images, videos, and audio.
 * - Compatible with React 19's head hoisting mechanism.
 * - TypeScript support for configuration options.
 *
 * Usage:
 * - Wrap your app with <MetaProvider defaults={globalOptions}> for application-wide defaults.
 * - Use <AllMeta basic={{ title: '...', description: '...' }} /> in components for overrides.
 *
 * @module AllMeta
 */
import React, { ReactNode, createContext, useContext } from "react"

// Type definitions, based on vite-plugin-open-graph with audio added for completeness
interface Options {
  basic?: BasicOptions
  twitter?: TwitterOptions
  facebook?: FacebookOptions
}

interface BasicOptions {
  title?: string
  type?: string
  image?: string | ImageOptions
  url?: string
  description?: string
  determiner?: "a" | "an" | "the" | "auto" | ""
  locale?: string
  localeAlternate?: string[]
  siteName?: string
  video?: string | VideoOptions
  audio?: string | AudioOptions // Added based on plugin example
}

interface ImageOptions {
  url?: string
  secureUrl?: string
  type?: string
  width?: number
  height?: number
  alt?: string
}

type VideoOptions = Omit<ImageOptions, "alt">
type AudioOptions = VideoOptions // Same structure as video in example

interface TwitterOptions {
  card?: "summary" | "summary_large_image" | "app" | "player"
  site?: string
  siteId?: string
  creator?: string
  creatorId?: string
  description?: string
  title?: string
  image?: string
  imageAlt?: string
  player?: string
  playerWidth?: number
  playerHeight?: number
  playerStream?: string
  app?: {
    name?: {
      iphone?: string
      ipad?: string
      googleplay?: string
    }
    id?: {
      iphone?: string
      ipad?: string
      googleplay?: string
    }
    url?: {
      iphone?: string
      ipad?: string
      googleplay?: string
    }
  }
}

interface FacebookOptions {
  appId?: number
}

// Context for global defaults
const MetaContext = createContext<Options | undefined>(undefined)

export function withMetaProvider(
  Component: React.ComponentType,
  defaults: Options = {},
) {
  return function MetaProviderWrapper(
    props: React.ComponentProps<typeof Component>,
  ) {
    return (
      <MetaContext.Provider value={defaults}>
        <Component {...props} />
      </MetaContext.Provider>
    )
  }
}

export function MetaProvider({
  children,
  defaults,
}: {
  children: ReactNode
  defaults: Options
}) {
  return (
    <MetaContext.Provider value={defaults}>{children}</MetaContext.Provider>
  )
}

// AllMeta component props (partial for overrides)
interface AllMetaProps {
  basic?: Partial<BasicOptions>
  twitter?: Partial<TwitterOptions>
  facebook?: Partial<FacebookOptions>
}

export function AllMeta(props: AllMetaProps) {
  const defaults = useContext(MetaContext) ?? {}
  const merged: Options = {
    basic: { ...defaults.basic, ...props.basic },
    twitter: { ...defaults.twitter, ...props.twitter },
    facebook: { ...defaults.facebook, ...props.facebook },
  }

  // Render function to generate tags based on merged options
  const renderTags = (options: Options): JSX.Element[] => {
    const elements: JSX.Element[] = []
    const { basic, twitter, facebook } = options

    // Basic tags
    if (basic?.title) {
      elements.push(<title key="title">{basic.title}</title>)
      elements.push(
        <meta key="og:title" property="og:title" content={basic.title} />,
      )
    }
    if (basic?.description) {
      elements.push(
        <meta
          key="description"
          name="description"
          content={basic.description}
        />,
      )
      elements.push(
        <meta
          key="og:description"
          property="og:description"
          content={basic.description}
        />,
      )
    }
    if (basic?.url) {
      elements.push(<meta key="og:url" property="og:url" content={basic.url} />)
    }
    if (basic?.type) {
      elements.push(
        <meta key="og:type" property="og:type" content={basic.type} />,
      )
    }
    if (basic?.determiner) {
      elements.push(
        <meta
          key="og:determiner"
          property="og:determiner"
          content={basic.determiner}
        />,
      )
    }
    if (basic?.locale) {
      elements.push(
        <meta key="og:locale" property="og:locale" content={basic.locale} />,
      )
    }
    if (basic?.localeAlternate) {
      basic.localeAlternate.forEach((loc, index) => {
        elements.push(
          <meta
            key={`og:locale:alternate_${index}`}
            property="og:locale:alternate"
            content={loc}
          />,
        )
      })
    }
    if (basic?.siteName) {
      elements.push(
        <meta
          key="og:site_name"
          property="og:site_name"
          content={basic.siteName}
        />,
      )
    }

    // Image
    if (basic?.image) {
      if (typeof basic.image === "string") {
        elements.push(
          <meta key="og:image" property="og:image" content={basic.image} />,
        )
      } else {
        if (basic.image.url)
          elements.push(
            <meta
              key="og:image:url"
              property="og:image"
              content={basic.image.url}
            />,
          )
        if (basic.image.secureUrl)
          elements.push(
            <meta
              key="og:image:secure_url"
              property="og:image:secure_url"
              content={basic.image.secureUrl}
            />,
          )
        if (basic.image.type)
          elements.push(
            <meta
              key="og:image:type"
              property="og:image:type"
              content={basic.image.type}
            />,
          )
        if (basic.image.width)
          elements.push(
            <meta
              key="og:image:width"
              property="og:image:width"
              content={String(basic.image.width)}
            />,
          )
        if (basic.image.height)
          elements.push(
            <meta
              key="og:image:height"
              property="og:image:height"
              content={String(basic.image.height)}
            />,
          )
        if (basic.image.alt)
          elements.push(
            <meta
              key="og:image:alt"
              property="og:image:alt"
              content={basic.image.alt}
            />,
          )
      }
    }

    // Video
    if (basic?.video) {
      if (typeof basic.video === "string") {
        elements.push(
          <meta key="og:video" property="og:video" content={basic.video} />,
        )
      } else {
        if (basic.video.url)
          elements.push(
            <meta
              key="og:video:url"
              property="og:video"
              content={basic.video.url}
            />,
          )
        if (basic.video.secureUrl)
          elements.push(
            <meta
              key="og:video:secure_url"
              property="og:video:secure_url"
              content={basic.video.secureUrl}
            />,
          )
        if (basic.video.type)
          elements.push(
            <meta
              key="og:video:type"
              property="og:video:type"
              content={basic.video.type}
            />,
          )
        if (basic.video.width)
          elements.push(
            <meta
              key="og:video:width"
              property="og:video:width"
              content={String(basic.video.width)}
            />,
          )
        if (basic.video.height)
          elements.push(
            <meta
              key="og:video:height"
              property="og:video:height"
              content={String(basic.video.height)}
            />,
          )
      }
    }

    // Audio (based on plugin example)
    if (basic?.audio) {
      if (typeof basic.audio === "string") {
        elements.push(
          <meta key="og:audio" property="og:audio" content={basic.audio} />,
        )
      } else {
        if (basic.audio.url)
          elements.push(
            <meta
              key="og:audio:url"
              property="og:audio"
              content={basic.audio.url}
            />,
          )
        if (basic.audio.secureUrl)
          elements.push(
            <meta
              key="og:audio:secure_url"
              property="og:audio:secure_url"
              content={basic.audio.secureUrl}
            />,
          )
        if (basic.audio.type)
          elements.push(
            <meta
              key="og:audio:type"
              property="og:audio:type"
              content={basic.audio.type}
            />,
          )
        if (basic.audio.width)
          elements.push(
            <meta
              key="og:audio:width"
              property="og:audio:width"
              content={String(basic.audio.width)}
            />,
          )
        if (basic.audio.height)
          elements.push(
            <meta
              key="og:audio:height"
              property="og:audio:height"
              content={String(basic.audio.height)}
            />,
          )
      }
    }

    // Twitter tags
    if (twitter?.card)
      elements.push(
        <meta key="twitter:card" name="twitter:card" content={twitter.card} />,
      )
    if (twitter?.site)
      elements.push(
        <meta key="twitter:site" name="twitter:site" content={twitter.site} />,
      )
    if (twitter?.siteId)
      elements.push(
        <meta
          key="twitter:site:id"
          name="twitter:site:id"
          content={twitter.siteId}
        />,
      )
    if (twitter?.creator)
      elements.push(
        <meta
          key="twitter:creator"
          name="twitter:creator"
          content={twitter.creator}
        />,
      )
    if (twitter?.creatorId)
      elements.push(
        <meta
          key="twitter:creator:id"
          name="twitter:creator:id"
          content={twitter.creatorId}
        />,
      )
    if (twitter?.description)
      elements.push(
        <meta
          key="twitter:description"
          name="twitter:description"
          content={twitter.description}
        />,
      )
    if (twitter?.title)
      elements.push(
        <meta
          key="twitter:title"
          name="twitter:title"
          content={twitter.title}
        />,
      )
    if (twitter?.image)
      elements.push(
        <meta
          key="twitter:image"
          name="twitter:image"
          content={twitter.image}
        />,
      )
    if (twitter?.imageAlt)
      elements.push(
        <meta
          key="twitter:image:alt"
          name="twitter:image:alt"
          content={twitter.imageAlt}
        />,
      )
    if (twitter?.player)
      elements.push(
        <meta
          key="twitter:player"
          name="twitter:player"
          content={twitter.player}
        />,
      )
    if (twitter?.playerWidth)
      elements.push(
        <meta
          key="twitter:player:width"
          name="twitter:player:width"
          content={String(twitter.playerWidth)}
        />,
      )
    if (twitter?.playerHeight)
      elements.push(
        <meta
          key="twitter:player:height"
          name="twitter:player:height"
          content={String(twitter.playerHeight)}
        />,
      )
    if (twitter?.playerStream)
      elements.push(
        <meta
          key="twitter:player:stream"
          name="twitter:player:stream"
          content={twitter.playerStream}
        />,
      )

    // Twitter app
    if (twitter?.app) {
      const app = twitter.app
      if (app.name?.iphone)
        elements.push(
          <meta
            key="twitter:app:name:iphone"
            name="twitter:app:name:iphone"
            content={app.name.iphone}
          />,
        )
      if (app.name?.ipad)
        elements.push(
          <meta
            key="twitter:app:name:ipad"
            name="twitter:app:name:ipad"
            content={app.name.ipad}
          />,
        )
      if (app.name?.googleplay)
        elements.push(
          <meta
            key="twitter:app:name:googleplay"
            name="twitter:app:name:googleplay"
            content={app.name.googleplay}
          />,
        )
      if (app.id?.iphone)
        elements.push(
          <meta
            key="twitter:app:id:iphone"
            name="twitter:app:id:iphone"
            content={app.id.iphone}
          />,
        )
      if (app.id?.ipad)
        elements.push(
          <meta
            key="twitter:app:id:ipad"
            name="twitter:app:id:ipad"
            content={app.id.ipad}
          />,
        )
      if (app.id?.googleplay)
        elements.push(
          <meta
            key="twitter:app:id:googleplay"
            name="twitter:app:id:googleplay"
            content={app.id.googleplay}
          />,
        )
      if (app.url?.iphone)
        elements.push(
          <meta
            key="twitter:app:url:iphone"
            name="twitter:app:url:iphone"
            content={app.url.iphone}
          />,
        )
      if (app.url?.ipad)
        elements.push(
          <meta
            key="twitter:app:url:ipad"
            name="twitter:app:url:ipad"
            content={app.url.ipad}
          />,
        )
      if (app.url?.googleplay)
        elements.push(
          <meta
            key="twitter:app:url:googleplay"
            name="twitter:app:url:googleplay"
            content={app.url.googleplay}
          />,
        )
    }

    // Facebook
    if (facebook?.appId) {
      elements.push(
        <meta
          key="fb:app_id"
          property="fb:app_id"
          content={String(facebook.appId)}
        />,
      )
    }

    return elements
  }

  return <>{renderTags(merged)}</>
}
