import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'ALMA Documentation',
  description: 'Autonomous Language Model Architecture - Infrastructure as Conversation',
  lang: 'en-US',
  
  // GitHub Pages deployment
  base: '/alma/',
  
  // Ignore dead links during build
  ignoreDeadLinks: true,
  
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/alma/favicon.svg' }],
    ['link', { rel: 'alternate icon', href: '/alma/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#ff6b35' }],
    ['meta', { name: 'apple-mobile-web-app-capable', content: 'yes' }],
    ['meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black' }]
  ],

  themeConfig: {
    logo: '/logo.svg',
    
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/QUICKSTART' },
      { text: 'API Reference', link: '/API_REFERENCE' },
      { 
        text: 'Resources',
        items: [
          { text: 'Architecture', link: '/ARCHITECTURE' },
          { text: 'Project Status', link: '/PROJECT_STATUS' },
          { text: 'Production Deployment', link: '/PRODUCTION_DEPLOYMENT' }
        ]
      }
    ],

    sidebar: [
      {
        text: 'Getting Started',
        collapsed: false,
        items: [
          { text: 'Introduction', link: '/INDEX' },
          { text: 'Quick Start', link: '/QUICKSTART' },
          { text: 'User Guide', link: '/USER_GUIDE' }
        ]
      },
      {
        text: 'Core Concepts',
        collapsed: false,
        items: [
          { text: 'Architecture', link: '/ARCHITECTURE' },
          { text: 'Blueprints', link: '/BLUEPRINTS' },
          { text: 'Infrastructure Pull Requests', link: '/IPR' },
          { text: 'Engines', link: '/ENGINES' }
        ]
      },
      {
        text: 'Advanced Features',
        collapsed: false,
        items: [
          { text: 'LLM Integration', link: '/LLM_GUIDE' },
          { text: 'Cognitive Layer', link: '/COGNITIVE_GUIDE' },
          { text: 'Streaming & Templates', link: '/STREAMING_AND_TEMPLATES' },
          { text: 'Rate Limiting & Metrics', link: '/RATE_LIMITING_AND_METRICS' }
        ]
      },
      {
        text: 'API Reference',
        collapsed: false,
        items: [
          { text: 'REST API', link: '/API_REFERENCE' },
          { text: 'API Overview', link: '/API' },
          { text: 'Tools API', link: '/TOOLS_API' }
        ]
      },
      {
        text: 'Deployment',
        collapsed: false,
        items: [
          { text: 'Production Deployment', link: '/PRODUCTION_DEPLOYMENT' },
          { text: 'Project Status', link: '/PROJECT_STATUS' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/fabriziosalmi/alma' }
    ],

    footer: {
      message: 'Released under the Apache 2.0 License.',
      copyright: 'Copyright © 2025 ALMA Project'
    },

    search: {
      provider: 'local'
    },

    editLink: {
      pattern: 'https://github.com/fabriziosalmi/alma/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    },

    lastUpdated: {
      text: 'Updated at',
      formatOptions: {
        dateStyle: 'full',
        timeStyle: 'medium'
      }
    }
  },

  markdown: {
    lineNumbers: true,
    theme: {
      light: 'github-light',
      dark: 'github-dark'
    }
  }
})
