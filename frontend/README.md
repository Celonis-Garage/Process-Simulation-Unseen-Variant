# Process Simulation Studio - Frontend

A modern, interactive web application for simulating and optimizing business process workflows with real-time KPI visualization.

## 🚀 Features

- **Interactive Process Explorer**: Visual drag-and-drop process modeling
- **AI-Powered Optimization**: Natural language prompts for process modifications
- **Real-time Simulation**: Instant KPI impact analysis
- **Event Log Visualization**: Comprehensive activity tracking and filtering
- **Responsive Design**: Built with React, TypeScript, and Tailwind CSS

## 📋 Prerequisites

- **Node.js** (v18 or higher)
- **npm** or **yarn** package manager

## 🛠️ Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## 🏗️ Tech Stack

- **React 18** with TypeScript
- **Vite** for fast builds
- **Tailwind CSS v4** for styling
- **shadcn/ui** component library
- **Radix UI** primitives
- **Zustand** for state management
- **Axios** for API communication
- **React DnD** for drag-and-drop

## 📦 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🔗 Backend Integration

This frontend connects to a FastAPI backend running on `http://localhost:8000`. Make sure the backend server is running for full functionality.

## 📚 Documentation

Additional documentation is available in the `src/` directory:
- `SETUP_GUIDE.md` - Detailed setup instructions
- `OPTIMIZATION_PROMPTS.md` - Sample prompts for process optimization
- `VERIFICATION_CHECKLIST.md` - KPI verification guide

## 📄 License

This project uses components from [shadcn/ui](https://ui.shadcn.com/) under MIT License.
