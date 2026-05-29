import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence } from 'framer-motion';

import Layout from '@components/Layout/Layout';
import Home from '@pages/Home';
import Generator from '@pages/Generator';
import Imager from '@pages/Imager';
import Templates from '@pages/Templates';
import BatchGenerator from '@pages/BatchGenerator';
import Settings from '@pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AnimatePresence mode="wait">
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Home />} />
              <Route path="/generator" element={<Generator />} />
              <Route path="/imager" element={<Imager />} />
              <Route path="/templates" element={<Templates />} />
              <Route path="/batch" element={<BatchGenerator />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
        </AnimatePresence>
      </BrowserRouter>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#1a1a2e',
            color: '#f1f0ff',
            border: '1px solid #2a2a45',
            borderRadius: '12px',
          },
          success: { iconTheme: { primary: '#10b981', secondary: '#1a1a2e' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#1a1a2e' } },
        }}
      />
    </QueryClientProvider>
  );
}
