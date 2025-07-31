import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import compression from 'vite-plugin-compression'
import imagemin from 'vite-plugin-imagemin'

// https://vitejs.dev/config/
export default defineConfig({
  // Build-time security: Hard-code test flags false in production
  define: {
    'import.meta.env.VITE_TEST_MODE': JSON.stringify(process.env.NODE_ENV === 'development' ? process.env.VITE_TEST_MODE || 'false' : 'false'),
    'import.meta.env.VITE_TEST_USER_ID': JSON.stringify(process.env.NODE_ENV === 'development' ? process.env.VITE_TEST_USER_ID || '' : ''),
  },

  plugins: [
    react(),
    // Gzip compression for production builds
    compression({
      algorithm: 'gzip',
      ext: '.gz',
    }),
    // Brotli compression for production builds
    compression({
      algorithm: 'brotliCompress',
      ext: '.br',
    }),
    // Image optimization
    imagemin({
      gifsicle: {
        optimizationLevel: 7,
        interlaced: false,
      },
      optipng: {
        optimizationLevel: 7,
      },
      mozjpeg: {
        quality: 80,
      },
      pngquant: {
        quality: [0.8, 0.9],
        speed: 4,
      },
      svgo: {
        plugins: [
          {
            name: 'removeViewBox',
            active: false,
          },
          {
            name: 'removeEmptyAttrs',
            active: false,
          },
        ],
      },
    }),
  ],

  // Base path for production
  base: './',

  // Path aliases
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@components": path.resolve(__dirname, "./components"),
      "@ui": path.resolve(__dirname, "./components/ui"),
      "@styles": path.resolve(__dirname, "./styles"),
      "@services": path.resolve(__dirname, "./src/services"),
      // Handle Figma asset imports
      "figma:asset": path.resolve(__dirname, "../static/images"),
    },
  },

  // Build configuration
  build: {
    // Output directory
    outDir: '../static/v2',

    // Clean output directory before build
    emptyOutDir: true,

    // Asset size warnings
    chunkSizeWarningLimit: 1000,

    // Rollup options for code splitting
    rollupOptions: {
      output: {
        // Manual chunks for better caching
        manualChunks: {
          // Vendor chunk for React and React DOM
          'vendor-react': ['react', 'react-dom'],
          // UI library chunks
          'vendor-ui': ['lucide-react', 'class-variance-authority', 'clsx', 'tailwind-merge'],
          // Radix UI components
          'vendor-radix': [
            '@radix-ui/react-slot',
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-select',
            '@radix-ui/react-tabs',
            '@radix-ui/react-accordion',
            '@radix-ui/react-avatar',
            '@radix-ui/react-checkbox',
            '@radix-ui/react-label',
            '@radix-ui/react-separator',
            '@radix-ui/react-switch',
            '@radix-ui/react-tooltip',
          ],
        },
        // Asset file naming with content hash
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `assets/images/[name]-[hash][extname]`
          } else if (/woff|woff2|eot|ttf|otf/i.test(ext)) {
            return `assets/fonts/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        },
        // Chunk file naming
        chunkFileNames: 'assets/js/[name]-[hash].js',
        // Entry file naming
        entryFileNames: 'assets/js/[name]-[hash].js',
      },
    },

    // Minification options
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },

    // Source maps for production debugging
    sourcemap: true,

    // CSS code splitting
    cssCodeSplit: true,

    // Target modern browsers
    target: 'es2020',
  },

  // Development server configuration
  server: {
    port: 3002,
    host: true,
    // Proxy API requests to backend
    proxy: {
      '/api': {
        target: 'http://localhost:8081',
        changeOrigin: true,
      },
    },
  },

  // CSS configuration
  css: {
    postcss: './postcss.config.js',
  },

  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'lucide-react',
      '@radix-ui/react-slot',
      'class-variance-authority',
      'clsx',
      'tailwind-merge',
    ],
  },
})
