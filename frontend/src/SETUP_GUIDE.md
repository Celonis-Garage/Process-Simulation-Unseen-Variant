# Process Simulation Studio - Local Setup Guide

This guide will help you replicate the entire "Process Simulation Studio" project locally on your machine.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18 or higher)
- **npm** or **yarn** package manager
- A modern code editor (VS Code recommended)

---

## 📦 Required Dependencies

### Core Dependencies

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }
}
```

### UI & Styling

```json
{
  "dependencies": {
    "tailwindcss": "^4.0.0",
    "lucide-react": "latest",
    "class-variance-authority": "latest",
    "clsx": "latest",
    "tailwind-merge": "latest"
  }
}
```

### Drag & Drop

```json
{
  "dependencies": {
    "react-dnd": "latest",
    "react-dnd-html5-backend": "latest"
  }
}
```

### Radix UI Components (for shadcn/ui)

```json
{
  "dependencies": {
    "@radix-ui/react-accordion": "latest",
    "@radix-ui/react-alert-dialog": "latest",
    "@radix-ui/react-aspect-ratio": "latest",
    "@radix-ui/react-avatar": "latest",
    "@radix-ui/react-checkbox": "latest",
    "@radix-ui/react-collapsible": "latest",
    "@radix-ui/react-context-menu": "latest",
    "@radix-ui/react-dialog": "latest",
    "@radix-ui/react-dropdown-menu": "latest",
    "@radix-ui/react-hover-card": "latest",
    "@radix-ui/react-label": "latest",
    "@radix-ui/react-menubar": "latest",
    "@radix-ui/react-navigation-menu": "latest",
    "@radix-ui/react-popover": "latest",
    "@radix-ui/react-progress": "latest",
    "@radix-ui/react-radio-group": "latest",
    "@radix-ui/react-scroll-area": "latest",
    "@radix-ui/react-select": "latest",
    "@radix-ui/react-separator": "latest",
    "@radix-ui/react-slider": "latest",
    "@radix-ui/react-slot": "latest",
    "@radix-ui/react-switch": "latest",
    "@radix-ui/react-tabs": "latest",
    "@radix-ui/react-toggle": "latest",
    "@radix-ui/react-toggle-group": "latest",
    "@radix-ui/react-tooltip": "latest",
    "cmdk": "latest",
    "date-fns": "latest",
    "embla-carousel-react": "latest",
    "input-otp": "latest",
    "react-day-picker": "latest",
    "react-resizable-panels": "latest",
    "recharts": "latest",
    "sonner": "^2.0.3",
    "vaul": "latest"
  }
}
```

### Dev Dependencies

```json
{
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.3",
    "vite": "^5.3.1"
  }
}
```

---

## 🚀 Quick Start Installation

### Option 1: Using npm

```bash
# Create a new Vite + React + TypeScript project
npm create vite@latest process-simulation-studio -- --template react-ts
cd process-simulation-studio

# Install core dependencies
npm install

# Install UI & styling libraries
npm install tailwindcss lucide-react class-variance-authority clsx tailwind-merge

# Install drag & drop
npm install react-dnd react-dnd-html5-backend

# Install Radix UI components (all at once)
npm install @radix-ui/react-accordion @radix-ui/react-alert-dialog \
  @radix-ui/react-aspect-ratio @radix-ui/react-avatar @radix-ui/react-checkbox \
  @radix-ui/react-collapsible @radix-ui/react-context-menu @radix-ui/react-dialog \
  @radix-ui/react-dropdown-menu @radix-ui/react-hover-card @radix-ui/react-label \
  @radix-ui/react-menubar @radix-ui/react-navigation-menu @radix-ui/react-popover \
  @radix-ui/react-progress @radix-ui/react-radio-group @radix-ui/react-scroll-area \
  @radix-ui/react-select @radix-ui/react-separator @radix-ui/react-slider \
  @radix-ui/react-slot @radix-ui/react-switch @radix-ui/react-tabs \
  @radix-ui/react-toggle @radix-ui/react-toggle-group @radix-ui/react-tooltip

# Install additional UI libraries
npm install cmdk date-fns embla-carousel-react input-otp \
  react-day-picker react-resizable-panels recharts sonner@2.0.3 vaul
```

### Option 2: Using yarn

```bash
# Create a new Vite + React + TypeScript project
yarn create vite process-simulation-studio --template react-ts
cd process-simulation-studio

# Install all dependencies
yarn add react react-dom
yarn add tailwindcss lucide-react class-variance-authority clsx tailwind-merge
yarn add react-dnd react-dnd-html5-backend
yarn add @radix-ui/react-accordion @radix-ui/react-alert-dialog \
  @radix-ui/react-aspect-ratio @radix-ui/react-avatar @radix-ui/react-checkbox \
  @radix-ui/react-collapsible @radix-ui/react-context-menu @radix-ui/react-dialog \
  @radix-ui/react-dropdown-menu @radix-ui/react-hover-card @radix-ui/react-label \
  @radix-ui/react-menubar @radix-ui/react-navigation-menu @radix-ui/react-popover \
  @radix-ui/react-progress @radix-ui/react-radio-group @radix-ui/react-scroll-area \
  @radix-ui/react-select @radix-ui/react-separator @radix-ui/react-slider \
  @radix-ui/react-slot @radix-ui/react-switch @radix-ui/react-tabs \
  @radix-ui/react-toggle @radix-ui/react-toggle-group @radix-ui/react-tooltip
yarn add cmdk date-fns embla-carousel-react input-otp \
  react-day-picker react-resizable-panels recharts sonner@2.0.3 vaul
```

---

## 📁 Project Structure

After installation, your project should have this structure:

```
process-simulation-studio/
├── public/
├── src/
│   ├── components/
│   │   ├── figma/
│   │   │   └── ImageWithFallback.tsx
│   │   ├── ui/
│   │   │   ├── accordion.tsx
│   │   │   ├── alert-dialog.tsx
│   │   │   ├── alert.tsx
│   │   │   ├── aspect-ratio.tsx
│   │   │   ├── avatar.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── breadcrumb.tsx
│   │   │   ├── button.tsx
│   │   │   ├── calendar.tsx
│   │   │   ├── card.tsx
│   │   │   ├── carousel.tsx
│   │   │   ├── chart.tsx
│   │   │   ├── checkbox.tsx
│   │   │   ├── collapsible.tsx
│   │   │   ├── command.tsx
│   │   │   ├── context-menu.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── drawer.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── form.tsx
│   │   │   ├── hover-card.tsx
│   │   │   ├── input-otp.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── menubar.tsx
│   │   │   ├── navigation-menu.tsx
│   │   │   ├── pagination.tsx
│   │   │   ├── popover.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── radio-group.tsx
│   │   │   ├── resizable.tsx
│   │   │   ├── scroll-area.tsx
│   │   │   ├── select.tsx
│   │   │   ├── separator.tsx
│   │   │   ├── sheet.tsx
│   │   │   ├── sidebar.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── slider.tsx
│   │   │   ├── sonner.tsx
│   │   │   ├── switch.tsx
│   │   │   ├── table.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── toggle-group.tsx
│   │   │   ├── toggle.tsx
│   │   │   ├── tooltip.tsx
│   │   │   ├── use-mobile.ts
│   │   │   └── utils.ts
│   │   ├── EventInfoDialog.tsx
│   │   ├── EventLogPanel.tsx
│   │   ├── EventPalette.tsx
│   │   ├── ProcessExplorer.tsx
│   │   ├── PromptPanel.tsx
│   │   ├── SimulationModal.tsx
│   │   └── TopBar.tsx
│   ├── styles/
│   │   └── globals.css
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## ⚙️ Configuration Files

### 1. `vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

### 2. `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    /* Path aliases */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 3. `tsconfig.node.json`

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

### 4. `package.json` (complete example)

```json
{
  "name": "process-simulation-studio",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "tailwindcss": "^4.0.0",
    "lucide-react": "latest",
    "class-variance-authority": "latest",
    "clsx": "latest",
    "tailwind-merge": "latest",
    "react-dnd": "latest",
    "react-dnd-html5-backend": "latest",
    "@radix-ui/react-accordion": "latest",
    "@radix-ui/react-alert-dialog": "latest",
    "@radix-ui/react-aspect-ratio": "latest",
    "@radix-ui/react-avatar": "latest",
    "@radix-ui/react-checkbox": "latest",
    "@radix-ui/react-collapsible": "latest",
    "@radix-ui/react-context-menu": "latest",
    "@radix-ui/react-dialog": "latest",
    "@radix-ui/react-dropdown-menu": "latest",
    "@radix-ui/react-hover-card": "latest",
    "@radix-ui/react-label": "latest",
    "@radix-ui/react-menubar": "latest",
    "@radix-ui/react-navigation-menu": "latest",
    "@radix-ui/react-popover": "latest",
    "@radix-ui/react-progress": "latest",
    "@radix-ui/react-radio-group": "latest",
    "@radix-ui/react-scroll-area": "latest",
    "@radix-ui/react-select": "latest",
    "@radix-ui/react-separator": "latest",
    "@radix-ui/react-slider": "latest",
    "@radix-ui/react-slot": "latest",
    "@radix-ui/react-switch": "latest",
    "@radix-ui/react-tabs": "latest",
    "@radix-ui/react-toggle": "latest",
    "@radix-ui/react-toggle-group": "latest",
    "@radix-ui/react-tooltip": "latest",
    "cmdk": "latest",
    "date-fns": "latest",
    "embla-carousel-react": "latest",
    "input-otp": "latest",
    "react-day-picker": "latest",
    "react-resizable-panels": "latest",
    "recharts": "latest",
    "sonner": "2.0.3",
    "vaul": "latest"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.3",
    "vite": "^5.3.1"
  }
}
```

### 5. `index.html`

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Process Simulation Studio</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### 6. `src/main.tsx`

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

---

## 🎨 Copying Files

### Required Files to Copy

After setting up the base project, copy all the following files from the existing project:

1. **Application Files:**
   - `src/App.tsx` - Main application component
   - `src/styles/globals.css` - Global styles with Tailwind v4 configuration

2. **Component Files:**
   - `src/components/EventInfoDialog.tsx`
   - `src/components/EventLogPanel.tsx`
   - `src/components/EventPalette.tsx`
   - `src/components/ProcessExplorer.tsx`
   - `src/components/PromptPanel.tsx`
   - `src/components/SimulationModal.tsx`
   - `src/components/TopBar.tsx`

3. **UI Components (all files from `src/components/ui/`):**
   - Copy all 47 files from the `components/ui/` directory

4. **Figma Components:**
   - `src/components/figma/ImageWithFallback.tsx`

---

## 🏃 Running the Application

Once you've installed all dependencies and copied all files:

```bash
# Start the development server
npm run dev
# or
yarn dev

# The application will be available at http://localhost:5173
```

---

## 🔧 Building for Production

```bash
# Build the application
npm run build
# or
yarn build

# Preview the production build
npm run preview
# or
yarn preview
```

---

## ✅ Verification Checklist

Before running, ensure:

- [ ] All dependencies are installed (check `package.json`)
- [ ] `src/App.tsx` is copied
- [ ] `src/styles/globals.css` is copied
- [ ] All 7 component files are in `src/components/`
- [ ] All 47 UI component files are in `src/components/ui/`
- [ ] `ImageWithFallback.tsx` is in `src/components/figma/`
- [ ] `index.html` is configured
- [ ] `main.tsx` imports `globals.css`
- [ ] Vite config has path aliases set up

---

## 🎯 Key Features to Test

After running the application, test these features:

1. **Prompt Panel (Left):**
   - Type natural language prompts
   - Click sample prompts
   - See AI responses

2. **Process Explorer (Center/Right):**
   - Zoom in/out with mouse wheel (Ctrl/Cmd + scroll)
   - Pan by dragging the canvas
   - Click `+` buttons to add steps
   - Drag steps to reorder them
   - Click time/cost badges to edit values
   - Remove steps with trash icon

3. **Event Palette (Far Right):**
   - Drag events from palette
   - Drop them between process steps
   - Collapse/expand the palette

4. **Event Log Panel (Bottom):**
   - View event logs table
   - Click "Simulate" button
   - See KPI changes in modal

5. **Simulation Modal:**
   - View before/after KPIs
   - See confidence meter
   - Read natural language summary
   - Understand "Why These KPI Changes?"

---

## 🐛 Troubleshooting

### Issue: Module not found errors

**Solution:** Make sure all dependencies are installed:
```bash
npm install
# or
yarn install
```

### Issue: Tailwind styles not working

**Solution:** Ensure `globals.css` is imported in `main.tsx`:
```tsx
import './styles/globals.css'
```

### Issue: Path alias errors

**Solution:** Check `vite.config.ts` has the path alias configured and `tsconfig.json` has the paths configured.

### Issue: TypeScript errors

**Solution:** Ensure `tsconfig.json` is configured correctly with all required compiler options.

---

## 📚 Additional Resources

- **Vite Documentation:** https://vitejs.dev/
- **React Documentation:** https://react.dev/
- **Tailwind CSS v4:** https://tailwindcss.com/
- **shadcn/ui:** https://ui.shadcn.com/
- **React DnD:** https://react-dnd.github.io/react-dnd/
- **Radix UI:** https://www.radix-ui.com/

---

## 💡 Tips

- Use **VS Code** with the following extensions:
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense
  - TypeScript and JavaScript Language Features

- For the best development experience:
  - Enable hot module replacement (HMR) in Vite
  - Use React DevTools browser extension
  - Install Redux DevTools if you add state management

---

## 📝 License

This project is for demonstration purposes.

---

## 🤝 Contributing

This is a prototype/demo project. Feel free to fork and modify as needed.

---

**Happy coding! 🚀**
